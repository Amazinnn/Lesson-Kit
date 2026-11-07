"""Confirmed course learning preferences: workspace file, HTTP adapter, failure semantics."""

import concurrent.futures
import json
import threading
import unittest
import urllib.request
from urllib.error import HTTPError

from tests.workbench.fixtures import WorkspaceFixture


class CoursePreferenceStoreTests(unittest.TestCase):
    """The Data writer owns the file; the browser is only a mirror."""

    def setUp(self):
        self.fixture = WorkspaceFixture()
        self.root = self.fixture.ws
        self.path = self.root / ".lessonkit" / "course-preferences.json"

    def tearDown(self):
        self.fixture.cleanup()

    def _envelope(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def test_explicit_values_round_trip_and_a_partial_update_keeps_the_rest(self):
        from workbench.data import course_preferences

        self.assertEqual(course_preferences.load_preferences(self.root, "dmath"), {})

        saved = course_preferences.save_preferences(self.root, "dmath", {
            "showRating": False,
            "submissionGranularity": "whole_problem",
        })
        self.assertEqual(
            saved, {"showRating": False, "submissionGranularity": "whole_problem"})
        self.assertEqual(course_preferences.load_preferences(self.root, "dmath"), saved)
        self.assertEqual(self._envelope()["course"], "dmath")
        self.assertEqual(
            set(self._envelope()), {"course", "values"},
            "the envelope carries the course identity and the values only")

        partial = course_preferences.save_preferences(
            self.root, "dmath", {"revealTiming": "on_submit"})
        self.assertEqual(partial, {
            "showRating": False,
            "submissionGranularity": "whole_problem",
            "revealTiming": "on_submit",
        })

    def test_absent_values_are_never_filled_with_defaults(self):
        from workbench.data import course_preferences

        course_preferences.save_preferences(self.root, "dmath", {"showRating": True})
        self.assertEqual(
            course_preferences.load_preferences(self.root, "dmath"),
            {"showRating": True},
            "an untouched field keeps whatever the entry point defaults to",
        )

    def test_secrets_appearance_and_unknown_fields_are_refused_without_writing(self):
        from workbench.data import course_preferences

        for values in (
            {"api_key": "sk-test"},
            {"provider": "pi"},
            {"theme": "night"},
            {"motion": False},
            {"sound": False},
            {"runningSendAction": "interrupt"},
            {"showRatings": True},
        ):
            with self.assertRaises(ValueError, msg=values):
                course_preferences.save_preferences(self.root, "dmath", values)
        self.assertFalse(self.path.exists(), "a refused write leaves no file")

    def test_invalid_types_and_choices_are_refused(self):
        from workbench.data import course_preferences

        for values in (
            {"showRating": "false"},
            {"showRating": 0},
            {"showSource": None},
            {"submissionGranularity": "per_question"},
            {"revealTiming": "never"},
            {"revealTiming": True},
        ):
            with self.assertRaises(ValueError, msg=values):
                course_preferences.save_preferences(self.root, "dmath", values)
        with self.assertRaises(ValueError):
            course_preferences.save_preferences(self.root, "dmath", {})
        with self.assertRaises(ValueError):
            course_preferences.save_preferences(self.root, "dmath", ["showRating"])
        self.assertFalse(self.path.exists())

    def test_corrupt_or_unknown_stored_data_fails_explicitly_and_is_never_overwritten(self):
        from workbench.data import course_preferences

        self.path.parent.mkdir(parents=True, exist_ok=True)
        for stored in (
            "{broken",
            "[]",
            json.dumps({"course": "dmath"}),
            json.dumps({"course": "dmath", "values": {"theme": "night"}}),
            json.dumps({"course": "", "values": {"showRating": True}}),
            json.dumps({"course": "dmath", "values": []}),
        ):
            self.path.write_text(stored, encoding="utf-8")
            with self.assertRaises(course_preferences.CorruptPreferences, msg=stored):
                course_preferences.load_preferences(self.root, "dmath")
            with self.assertRaises(course_preferences.CorruptPreferences, msg=stored):
                course_preferences.save_preferences(
                    self.root, "dmath", {"showRating": True})
            self.assertEqual(self.path.read_text(encoding="utf-8"), stored)

    def test_another_course_projection_is_not_read_or_overwritten(self):
        from workbench.data import course_preferences

        course_preferences.save_preferences(self.root, "dmath", {"showRating": False})
        self.assertEqual(course_preferences.load_preferences(self.root, "os"), {})

        with self.assertRaises(ValueError):
            course_preferences.save_preferences(self.root, "os", {"showRating": True})
        self.assertEqual(
            course_preferences.load_preferences(self.root, "dmath"),
            {"showRating": False},
            "a different course never overwrites the stored projection",
        )

    def test_concurrent_saves_keep_every_explicit_value(self):
        from workbench.data import course_preferences

        values = [
            {"showRating": False},
            {"showSource": True},
            {"submissionGranularity": "whole_problem"},
            {"revealTiming": "on_submit"},
        ]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(
                lambda item: course_preferences.save_preferences(self.root, "dmath", item),
                values,
            ))

        stored = course_preferences.load_preferences(self.root, "dmath")
        self.assertEqual(stored, {
            "showRating": False,
            "showSource": True,
            "submissionGranularity": "whole_problem",
            "revealTiming": "on_submit",
        })

    def test_an_interrupted_write_leaves_no_partial_file(self):
        from workbench.data import course_preferences
        from unittest import mock

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"course": "dmath", "values": {"showRating": False}}),
            encoding="utf-8",
        )
        with mock.patch.object(
            course_preferences, "_publish", side_effect=OSError("disk is full")
        ):
            with self.assertRaises(OSError):
                course_preferences.save_preferences(
                    self.root, "dmath", {"showRating": True})

        self.assertEqual(
            course_preferences.load_preferences(self.root, "dmath"),
            {"showRating": False},
        )
        self.assertEqual(
            [item.name for item in self.path.parent.iterdir() if item.name != "course-preferences.json"],
            [],
            "the temporary file of a failed write is removed",
        )


class CoursePreferenceApiTests(unittest.TestCase):
    """GET/PATCH stay thin: they route to the same writer and reader."""

    def setUp(self):
        self.fixture = WorkspaceFixture()
        from workbench.server import app
        self.server = app.create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.root = self.fixture.ws
        self.path = self.root / ".lessonkit" / "course-preferences.json"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.fixture.cleanup()

    def _request(self, method, path, payload=None):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=None if payload is None else json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def _error(self, method, path, payload=None):
        with self.assertRaises(HTTPError) as caught:
            self._request(method, path, payload)
        return caught.exception.code, json.loads(caught.exception.read().decode("utf-8"))

    def test_absent_projection_reads_as_unsaved_rather_than_defaults(self):
        status, data = self._request("GET", "/api/w/dmath/course-preferences")
        self.assertEqual(status, 200)
        self.assertEqual(data, {"saved": False, "values": {}})
        self.assertFalse(self.path.exists(), "reading never materializes the file")

    def test_patch_saves_and_get_returns_the_confirmed_values(self):
        status, saved = self._request(
            "PATCH", "/api/w/dmath/course-preferences",
            {"showRating": False, "revealTiming": "on_submit"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(saved["saved"], True)
        self.assertEqual(
            saved["values"], {"showRating": False, "revealTiming": "on_submit"})

        status, loaded = self._request("GET", "/api/w/dmath/course-preferences")
        self.assertEqual(status, 200)
        self.assertEqual(loaded, saved)

    def test_patch_is_a_partial_update(self):
        self._request(
            "PATCH", "/api/w/dmath/course-preferences",
            {"showRating": False, "showSource": True},
        )
        status, data = self._request(
            "PATCH", "/api/w/dmath/course-preferences",
            {"submissionGranularity": "whole_problem"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["values"], {
            "showRating": False,
            "showSource": True,
            "submissionGranularity": "whole_problem",
        })

    def test_invalid_input_is_a_400_and_writes_nothing(self):
        for payload in (
            {},
            {"theme": "night"},
            {"showRating": "false"},
            {"submissionGranularity": "per_question"},
        ):
            status, data = self._error(
                "PATCH", "/api/w/dmath/course-preferences", payload)
            self.assertEqual(status, 400, data)
        self.assertFalse(self.path.exists())

    def test_a_corrupt_projection_is_an_explicit_failure(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{broken", encoding="utf-8")

        status, data = self._error("GET", "/api/w/dmath/course-preferences")
        self.assertEqual(status, 500, data)
        status, data = self._error(
            "PATCH", "/api/w/dmath/course-preferences", {"showRating": True})
        self.assertEqual(status, 500, data)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{broken")

    def test_unknown_workspace_is_a_404(self):
        status, data = self._error("GET", "/api/w/nope/course-preferences")
        self.assertEqual(status, 404, data)


if __name__ == "__main__":
    unittest.main()
