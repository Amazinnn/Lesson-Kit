"""The declared CLI/API surface must match the code it describes.

The readable tables live in docs/action-graph/L2-interfaces.md; workbench/surface.py
is the machine authority. These tests fail when a route or command is added,
renamed, or removed without the declaration following it — which is exactly how
the counts drifted before (31/20 written down, 32/22 in the code).
"""

import unittest

from workbench import surface
from workbench.cli.main import command_names
from workbench.server import app


class DeclaredSurfaceTests(unittest.TestCase):
    def test_every_declared_command_exists_and_every_command_is_declared(self):
        real = set(command_names())
        declared = set(surface.COMMANDS)
        self.assertEqual(sorted(real - declared), [],
                         "commands exist but are not declared in workbench/surface.py")
        self.assertEqual(sorted(declared - real), [],
                         "commands are declared but do not exist in the parser")

    def test_every_declared_route_exists_and_every_route_is_declared(self):
        real = {(method, path) for method, path, _ in app.ROUTES}
        declared = set(surface.ROUTES)
        self.assertEqual(sorted(real - declared), [],
                         "routes exist but are not declared in workbench/surface.py")
        self.assertEqual(sorted(declared - real), [],
                         "routes are declared but are not in app.ROUTES")

    def test_agent_reachable_routes_name_a_real_command(self):
        commands = set(command_names())
        for key, (audience, served_by, _) in surface.ROUTES.items():
            with self.subTest(route=key):
                self.assertIn(audience, surface.AUDIENCES)
                if audience in (surface.AGENT, surface.BOTH):
                    self.assertTrue(
                        served_by, f"{key} claims Agent reachability but names no command")
                for name in served_by:
                    self.assertIn(name, commands,
                                  f"{key} names a command that does not exist: {name}")

    def test_browser_only_entries_carry_their_reason(self):
        for key, (audience, served_by, note) in surface.ROUTES.items():
            with self.subTest(route=key):
                if audience == surface.BROWSER:
                    self.assertTrue(note, f"{key} is browser-only without a reason")
                    self.assertEqual(served_by, (),
                                     f"{key} is browser-only but names a serving command")
        for name, (audience, note) in surface.COMMANDS.items():
            with self.subTest(command=name):
                self.assertIn(audience, surface.AUDIENCES)
                if audience == surface.BROWSER:
                    self.assertTrue(note, f"{name} is browser-only without a reason")

    def test_both_surface_entries_are_implemented_on_both_sides(self):
        real_routes = {(method, path) for method, path, _ in app.ROUTES}
        commands = set(command_names())
        for key, (audience, served_by, _) in surface.ROUTES.items():
            if audience != surface.BOTH:
                continue
            with self.subTest(route=key):
                self.assertIn(key, real_routes)
                self.assertTrue(served_by)
                self.assertTrue(set(served_by) <= commands)
        for name, (audience, _) in surface.COMMANDS.items():
            if audience != surface.BOTH:
                continue
            with self.subTest(command=name):
                self.assertIn(name, commands)


if __name__ == "__main__":
    unittest.main()
