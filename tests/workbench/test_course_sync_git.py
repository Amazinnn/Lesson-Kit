"""System Git transport for course sync: managed paths only, no destructive local moves."""

import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


def git(cwd, *args, check=True):
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and completed.returncode:
        raise AssertionError(
            f"git {' '.join(args)} failed ({completed.returncode}): {completed.stderr}"
        )
    return completed


class GitTransportCase(unittest.TestCase):
    branch = "main"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.remote = root / "course-remote.git"
        self.repo = root / "course"
        git(root, "init", "--bare", "-b", self.branch, str(self.remote))
        git(root, "init", "-b", self.branch, str(self.repo))
        git(self.repo, "config", "user.name", "Sync Test")
        git(self.repo, "config", "user.email", "sync@example.com")
        git(self.repo, "config", "commit.gpgsign", "false")
        git(self.repo, "remote", "add", "origin", str(self.remote))
        self.write("README.md", "# course\n")
        self.commit("chore: init")

    # -- fixtures ---------------------------------------------------------
    def write(self, relative, text):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_bytes(self, relative, payload):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", message)
        return self.head()

    def head(self):
        return git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def status(self):
        return git(self.repo, "status", "--porcelain=v1").stdout

    def commit_subject(self):
        return git(self.repo, "log", "-1", "--pretty=%s").stdout.strip()

    def committed_paths(self):
        out = git(self.repo, "show", "--pretty=format:", "--name-only", "HEAD").stdout
        return sorted(path for path in out.splitlines() if path.strip())

    def remote_head(self, branch=None):
        out = git(
            self.repo, "ls-remote", str(self.remote), f"refs/heads/{branch or self.branch}"
        ).stdout.strip()
        return out.split("\t")[0] if out else None

    def test_commit_keeps_concurrently_staged_foreign_file_outside_commit(self):
        from workbench.bridge import git_sync

        self.write('managed.md', 'course change')
        self.write('other.md', 'concurrent work')
        actual_git = git_sync._git

        def stage_before_commit(repo, *args, **kwargs):
            if args[0] == 'commit':
                git(repo, 'add', '--', 'other.md')
            return actual_git(repo, *args, **kwargs)

        with patch.object(git_sync, '_git', side_effect=stage_before_commit):
            result = git_sync.publish(self.repo, self.branch, ['managed.md'])
        self.assertEqual(result['remote']['status'], 'published')
        self.assertEqual(self.committed_paths(), ['managed.md'])
        self.assertEqual(git(self.repo, 'diff', '--cached', '--name-only').stdout.strip(), 'other.md')

    def test_git_metacharacters_in_names_are_literal(self):
        from workbench.bridge import git_sync

        self.write('[ab].md', 'literal name')
        self.write('a.md', 'unrelated name')
        git_sync.publish(self.repo, self.branch, ['[ab].md'])
        self.assertEqual(self.committed_paths(), ['[ab].md'])
        self.assertIn('?? a.md', self.status())

    def test_windows_git_metadata_aliases_are_rejected(self):
        from workbench.bridge import git_sync

        for name in ('.GIT/config', '.git./config', 'notes./file.md'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                git_sync.publish(self.repo, self.branch, [name])

    def test_sanitize_removes_query_and_url_credentials(self):
        from workbench.bridge import git_sync

        message = git_sync.sanitize('https://user:password@host/repo?access_token=secret&branch=main')
        self.assertNotIn('password', message)
        self.assertNotIn('secret', message)
        self.assertIn('branch=main', message)

    def advance_remote(self, relative="notes.md", text="remote change\n"):
        """Publish a commit from another installation, so the local clone diverges."""
        clone = self.repo.parent / "other-clone"
        git(clone.parent, "clone", "--quiet", str(self.remote), str(clone))
        git(clone, "config", "user.name", "Other Installation")
        git(clone, "config", "user.email", "other@example.com")
        git(clone, "config", "commit.gpgsign", "false")
        (clone / relative).parent.mkdir(parents=True, exist_ok=True)
        (clone / relative).write_text(text, encoding="utf-8")
        git(clone, "add", "-A")
        git(clone, "commit", "--quiet", "-m", "other: remote change")
        git(clone, "push", "--quiet", "origin", f"HEAD:{self.branch}")
        return git(clone, "rev-parse", "HEAD").stdout.strip()

    # -- publish ----------------------------------------------------------
    def test_publish_commits_stages_and_pushes_only_managed_paths(self):
        from workbench.bridge import git_sync

        self.write("goals.json", '{"goal": "finish ch06"}')
        self.write("notes/plan.md", "step one\n")
        self.write("scratch.md", "unmanaged working note\n")

        result = git_sync.publish(
            str(self.repo),
            self.branch,
            ["goals.json", "notes/plan.md"],
            message="Sync managed course files",
        )

        head = self.head()
        self.assertEqual(result["local"]["status"], "committed")
        self.assertEqual(result["local"]["commit"], head)
        self.assertEqual(result["local"]["created_commit"], head)
        self.assertEqual(
            sorted(result["local"]["changed_paths"]), ["goals.json", "notes/plan.md"]
        )
        self.assertEqual(self.committed_paths(), ["goals.json", "notes/plan.md"])
        self.assertEqual(self.commit_subject(), "Sync managed course files")

        self.assertEqual(result["remote"]["status"], "published")
        self.assertEqual(result["remote"]["commit"], head)
        self.assertEqual(self.remote_head(), head)

        scratch = self.repo / "scratch.md"
        self.assertEqual(scratch.read_text(encoding="utf-8"), "unmanaged working note\n")
        self.assertIn("?? scratch.md", self.status())

    def test_publish_creates_no_commit_when_nothing_changed(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "first\n")
        first = git_sync.publish(str(self.repo), self.branch, ["notes.md"])
        first_head = self.head()

        second = git_sync.publish(str(self.repo), self.branch, ["notes.md"])

        self.assertEqual(second["local"]["status"], "unchanged")
        self.assertIsNone(second["local"]["created_commit"])
        self.assertEqual(second["local"]["commit"], first_head)
        self.assertEqual(second["local"]["changed_paths"], [])
        self.assertEqual(self.head(), first_head)
        self.assertEqual(second["remote"]["status"], "unchanged")
        self.assertEqual(second["remote"]["commit"], first["remote"]["commit"])

    def test_publish_leaves_unrelated_worktree_changes_untouched(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "managed\n")
        self.write("README.md", "# course edited elsewhere\n")
        self.write("draft.md", "unfinished\n")
        git(self.repo, "add", "notes.md")

        result = git_sync.publish(str(self.repo), self.branch, ["notes.md"])

        self.assertEqual(result["local"]["status"], "committed")
        self.assertEqual(self.committed_paths(), ["notes.md"])
        self.assertEqual(
            (self.repo / "README.md").read_text(encoding="utf-8"),
            "# course edited elsewhere\n",
        )
        self.assertEqual(
            (self.repo / "draft.md").read_text(encoding="utf-8"), "unfinished\n"
        )
        status = self.status()
        self.assertIn(" M README.md", status)
        self.assertIn("?? draft.md", status)

    def test_publish_refuses_unrelated_staged_files(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "managed\n")
        self.write("other.md", "somebody else's staged work\n")
        git(self.repo, "add", "other.md")
        head = self.head()

        with self.assertRaises(ValueError) as caught:
            git_sync.publish(str(self.repo), self.branch, ["notes.md"])

        self.assertIn("other.md", str(caught.exception))
        self.assertEqual(self.head(), head)
        self.assertIn("A  other.md", self.status())
        self.assertEqual((self.repo / "notes.md").read_text(encoding="utf-8"), "managed\n")
        self.assertIsNone(self.remote_head())

    def test_publish_reports_rejected_push_without_force(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "first\n")
        first = git_sync.publish(str(self.repo), self.branch, ["notes.md"])
        remote_commit = self.advance_remote()

        self.write("notes.md", "local change\n")
        result = git_sync.publish(str(self.repo), self.branch, ["notes.md"])

        head = self.head()
        self.assertEqual(result["local"]["status"], "committed")
        self.assertEqual(result["local"]["commit"], head)
        self.assertNotEqual(head, first["local"]["commit"])
        self.assertEqual(
            (self.repo / "notes.md").read_text(encoding="utf-8"), "local change\n"
        )

        self.assertEqual(result["remote"]["status"], "failed")
        reason = result["remote"]["reason"].lower()
        self.assertTrue("non-fast-forward" in reason or "rejected" in reason, reason)
        self.assertEqual(self.remote_head(), remote_commit)
        self.assertEqual(result["remote"]["commit"], remote_commit)

    def test_publish_publishes_a_pending_commit_without_new_changes(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "first\n")
        git(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://learner:secret-token@127.0.0.1:9/course.git",
        )
        failed = git_sync.publish(str(self.repo), self.branch, ["notes.md"])
        self.assertEqual(failed["local"]["status"], "committed")
        self.assertEqual(failed["remote"]["status"], "failed")
        local_commit = failed["local"]["commit"]

        git(self.repo, "remote", "set-url", "origin", str(self.remote))
        retried = git_sync.publish(str(self.repo), self.branch, ["notes.md"])

        self.assertEqual(retried["local"]["status"], "unchanged")
        self.assertEqual(retried["local"]["commit"], local_commit)
        self.assertEqual(retried["remote"]["status"], "published")
        self.assertEqual(self.remote_head(), local_commit)

    def test_publish_allows_managed_deletions(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "first\n")
        self.write("old/plan.md", "obsolete\n")
        git_sync.publish(str(self.repo), self.branch, ["notes.md", "old/plan.md"])

        (self.repo / "old" / "plan.md").unlink()
        result = git_sync.publish(
            str(self.repo), self.branch, ["notes.md", "old/plan.md"]
        )

        self.assertEqual(result["local"]["status"], "committed")
        self.assertEqual(sorted(result["local"]["changed_paths"]), ["old/plan.md"])
        tracked = git(self.repo, "ls-tree", "-r", "--name-only", "HEAD").stdout.split()
        self.assertNotIn("old/plan.md", tracked)
        self.assertEqual(result["remote"]["status"], "published")

    def test_publish_rejects_paths_outside_the_repository(self):
        from workbench.bridge import git_sync

        self.write("sub/inner.md", "inner\n")
        head = self.head()
        for bad in [
            "../escape.md",
            "/absolute.md",
            "C:/absolute.md",
            ".git/config",
            "sub/.git/config",
            "",
            "sub",
        ]:
            with self.subTest(path=bad):
                with self.assertRaises(ValueError):
                    git_sync.publish(str(self.repo), self.branch, [bad])
                self.assertEqual(self.head(), head)
                self.assertIsNone(self.remote_head())

    def test_publish_requires_the_configured_branch_checked_out(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "managed\n")
        git(self.repo, "checkout", "-b", "other-branch")
        other_head = self.head()

        with self.assertRaises(ValueError) as caught:
            git_sync.publish(str(self.repo), self.branch, ["notes.md"])

        self.assertIn(self.branch, str(caught.exception))
        self.assertEqual(self.head(), other_head)
        self.assertEqual((self.repo / "notes.md").read_text(encoding="utf-8"), "managed\n")
        self.assertIsNone(self.remote_head())

    # -- remote reading ---------------------------------------------------
    def test_remote_files_read_are_binary_safe(self):
        from workbench.bridge import git_sync

        payload = b"\x89PNG\r\n\x1a\n\x00\x01\xfe\xff binary bytes"
        self.write_bytes("figures/chart.png", payload)
        published = git_sync.publish(
            str(self.repo), self.branch, ["figures/chart.png"]
        )

        remote = git_sync.read_remote_files(
            str(self.repo),
            published["remote"]["commit"],
            ["figures/chart.png", "figures/missing.png"],
        )

        self.assertEqual(remote["files"]["figures/chart.png"], payload)
        self.assertEqual(remote["missing"], ["figures/missing.png"])
        self.assertEqual(remote["commit"], published["remote"]["commit"])

    def test_read_remote_files_rejects_directories(self):
        from workbench.bridge import git_sync

        self.write("figures/chart.png", "png\n")
        published = git_sync.publish(str(self.repo), self.branch, ["figures/chart.png"])

        with self.assertRaises(ValueError):
            git_sync.read_remote_files(
                str(self.repo), published["local"]["commit"], ["figures"]
            )

    def test_read_remote_files_rejects_symbolic_links(self):
        from workbench.bridge import git_sync

        self.write("alias-target.md", "real content\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--quiet", "-m", "chore: target")
        blob = git(self.repo, "rev-parse", ":alias-target.md").stdout.strip()
        git(self.repo, "update-index", "--add", "--cacheinfo", f"120000,{blob},alias.md")
        git(self.repo, "commit", "--quiet", "-m", "chore: link")
        link_commit = self.head()

        with self.assertRaises(ValueError):
            git_sync.read_remote_files(str(self.repo), link_commit, ["alias.md"])

    def test_fetch_reports_remote_commit_without_touching_local_work(self):
        from workbench.bridge import git_sync

        self.write("notes.md", "first\n")
        git_sync.publish(str(self.repo), self.branch, ["notes.md"])
        local_head = self.head()
        self.write("README.md", "uncommitted local edit\n")
        remote_commit = self.advance_remote(text="remote second\n")
        branches_before = git(self.repo, "for-each-ref", "refs/heads").stdout

        fetched = git_sync.fetch_remote(str(self.repo), self.branch)

        self.assertEqual(fetched["commit"], remote_commit)
        self.assertEqual(self.head(), local_head)
        self.assertEqual(
            (self.repo / "README.md").read_text(encoding="utf-8"),
            "uncommitted local edit\n",
        )
        self.assertIn(" M README.md", self.status())
        self.assertEqual(
            git(self.repo, "for-each-ref", "refs/heads").stdout, branches_before
        )
        remote_files = git_sync.read_remote_files(
            str(self.repo), fetched["commit"], ["notes.md"]
        )
        self.assertEqual(remote_files["files"]["notes.md"], b"remote second\n")

    def test_fetch_error_hides_credentials_from_the_remote_url(self):
        from workbench.bridge import git_sync

        git(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://learner:secret-token@127.0.0.1:9/course.git",
        )

        with self.assertRaises(RuntimeError) as caught:
            git_sync.fetch_remote(str(self.repo), self.branch)

        self.assertNotIn("secret-token", message := str(caught.exception))
        self.assertNotIn("learner", message)

    # -- inspection -------------------------------------------------------
    def test_inspect_reports_state_without_mutating_the_repository(self):
        from workbench.bridge import git_sync

        self.write("staged.md", "staged\n")
        git(self.repo, "add", "staged.md")
        self.write("README.md", "modified\n")
        self.write("loose.md", "untracked\n")
        before = (
            self.head(),
            self.status(),
            git(self.repo, "for-each-ref").stdout,
        )

        state = git_sync.inspect_repository(str(self.repo), self.branch)

        self.assertEqual(state["head_branch"], self.branch)
        self.assertEqual(state["head_commit"], self.head())
        self.assertTrue(state["branch_checked_out"])
        self.assertFalse(state["repository_clean"])
        self.assertEqual(state["staged_paths"], ["staged.md"])
        self.assertIn("README.md", state["modified_paths"])
        self.assertIn("loose.md", state["untracked_paths"])
        self.assertIsNone(state["tracking_commit"])
        self.assertEqual(state["remote_url"], str(self.remote))
        self.assertEqual(
            (self.head(), self.status(), git(self.repo, "for-each-ref").stdout), before
        )

    def test_inspect_sanitizes_credentials_in_the_remote_url(self):
        from workbench.bridge import git_sync

        git(
            self.repo,
            "remote",
            "set-url",
            "origin",
            "https://learner:secret-token@example.com/course.git",
        )

        state = git_sync.inspect_repository(str(self.repo), self.branch)

        self.assertNotIn("secret-token", state["remote_url"])
        self.assertIn("***@", state["remote_url"])


if __name__ == "__main__":
    unittest.main()
