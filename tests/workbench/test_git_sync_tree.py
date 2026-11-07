"""Remote file listing under one directory: regular blobs only, never followed."""

import subprocess
import tempfile
import unittest
from pathlib import Path


def git(cwd, *args, check=True, stdin=None):
    redirect = {"input": stdin} if stdin is not None else {"stdin": subprocess.DEVNULL}
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        **redirect,
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


class RemoteTreeCase(unittest.TestCase):
    """Real local repositories: the listing reads a commit, never the worktree."""

    branch = "main"

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "course"
        git(self.root, "init", "-q", "-b", self.branch, str(self.repo))
        git(self.repo, "config", "user.name", "Tree Test")
        git(self.repo, "config", "user.email", "tree@example.com")
        git(self.repo, "config", "commit.gpgsign", "false")

    # -- fixtures ---------------------------------------------------------
    def write(self, relative, text):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def commit(self, message):
        git(self.repo, "add", "-A")
        return self.commit_index(message)

    def commit_index(self, message):
        """Commit exactly the index, so staged trees, links and gitlinks survive."""
        git(self.repo, "commit", "--quiet", "-m", message)
        return self.head()

    def head(self):
        return git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def blob_of(self, relative):
        return git(self.repo, "rev-parse", f":{relative}").stdout.strip()

    def stage_entry(self, mode, sha, relative):
        git(self.repo, "update-index", "--add", "--cacheinfo", f"{mode},{sha},{relative}")

    def commit_empty_directory(self, relative):
        """A commit whose tree carries an existing directory with no entries."""
        empty = git(self.repo, "mktree").stdout.strip()
        tree = git(self.repo, "mktree", stdin=f"040000 tree {empty}\t{relative}\n").stdout.strip()
        return git(
            self.repo, "commit-tree", tree, "-p", self.head(), stdin="chore: empty\n"
        ).stdout.strip()

    # -- listing ----------------------------------------------------------
    def test_lists_nested_regular_files_repository_relative(self):
        from workbench.bridge import git_sync

        self.write("README.md", "# course\n")
        self.write("files/notes/plan.md", "plan\n")
        self.write("files/figures/chart.png", "png\n")
        commit = self.commit("chore: course files")

        listed = git_sync.list_remote_files(str(self.repo), commit, "files")

        self.assertEqual(
            listed, ["files/figures/chart.png", "files/notes/plan.md"]
        )
        self.assertNotIn("README.md", listed)

    def test_preserves_unicode_spaces_and_sorted_order(self):
        from workbench.bridge import git_sync

        self.write("files/b 笔记.md", "b\n")
        self.write("files/a 题目 一.md", "a\n")
        self.write("files/子目录/第 1 题.md", "1\n")
        commit = self.commit("chore: unicode")

        listed = git_sync.list_remote_files(str(self.repo), commit, "files")

        self.assertEqual(
            listed,
            ["files/a 题目 一.md", "files/b 笔记.md", "files/子目录/第 1 题.md"],
        )
        self.assertEqual(git_sync.list_remote_files(str(self.repo), commit, "files"), listed)

    def test_missing_and_empty_directories_list_nothing(self):
        from workbench.bridge import git_sync

        self.write("files/notes.md", "n\n")
        commit = self.commit("chore: files")
        empty_commit = self.commit_empty_directory("packages")

        self.assertEqual(git_sync.list_remote_files(str(self.repo), commit, "files/missing"), [])
        self.assertEqual(git_sync.list_remote_files(str(self.repo), commit, "nowhere"), [])
        self.assertEqual(
            git_sync.list_remote_files(str(self.repo), empty_commit, "packages"), []
        )

    def test_directory_prefix_is_exact_not_a_sibling(self):
        from workbench.bridge import git_sync

        self.write("files/a.md", "a\n")
        self.write("files-old/b.md", "b\n")
        self.write("filesX/c.md", "c\n")
        self.write("files.md", "f\n")
        self.write("notes/files/d.md", "d\n")
        commit = self.commit("chore: siblings")

        self.assertEqual(
            git_sync.list_remote_files(str(self.repo), commit, "files"), ["files/a.md"]
        )
        self.assertEqual(
            git_sync.list_remote_files(str(self.repo), commit, "files-old"), ["files-old/b.md"]
        )

    def test_lists_only_the_requested_commit(self):
        from workbench.bridge import git_sync

        self.write("files/a.md", "a\n")
        first = self.commit("chore: first")
        self.write("files/b.md", "b\n")
        second = self.commit("chore: second")

        self.assertEqual(git_sync.list_remote_files(str(self.repo), first, "files"), ["files/a.md"])
        self.assertEqual(
            git_sync.list_remote_files(str(self.repo), second, "files"),
            ["files/a.md", "files/b.md"],
        )

    # -- rejection --------------------------------------------------------
    def test_rejects_unsafe_directory_arguments(self):
        from workbench.bridge import git_sync

        self.write("files/a.md", "a\n")
        commit = self.commit("chore: files")

        for bad in [
            "../escape",
            "files/../../escape",
            "/absolute",
            "C:/absolute",
            ".git",
            "files/.git/objects",
            "",
            "   ",
            "files ",
            "files.",
            "sub/..",
            None,
            42,
            ["files"],
        ]:
            with self.subTest(directory=bad), self.assertRaises(ValueError):
                git_sync.list_remote_files(str(self.repo), commit, bad)

    def test_rejects_unsafe_or_unknown_commits(self):
        from workbench.bridge import git_sync

        self.write("files/a.md", "a\n")
        self.commit("chore: files")

        for bad in ["", "-n1", "HEAD extra", "deadbeef" * 5, "refs/heads/missing", None, 7]:
            with self.subTest(commit=bad), self.assertRaises(ValueError):
                git_sync.list_remote_files(str(self.repo), bad, "files")

    def test_rejects_a_file_instead_of_a_directory(self):
        from workbench.bridge import git_sync

        self.write("files.md", "f\n")
        commit = self.commit("chore: file")

        with self.assertRaises(ValueError):
            git_sync.list_remote_files(str(self.repo), commit, "files.md")

    def test_rejects_symbolic_link_entries_inside_the_directory(self):
        from workbench.bridge import git_sync

        self.write("files/target.md", "real content\n")
        self.commit("chore: target")
        self.stage_entry("120000", self.blob_of("files/target.md"), "files/alias.md")
        commit = self.commit_index("chore: link")

        with self.assertRaises(ValueError) as caught:
            git_sync.list_remote_files(str(self.repo), commit, "files")

        self.assertIn("files/alias.md", str(caught.exception))

    def test_rejects_submodule_entries_inside_the_directory(self):
        from workbench.bridge import git_sync

        self.write("files/a.md", "a\n")
        base = self.commit("chore: base")
        self.stage_entry("160000", base, "files/vendor")
        commit = self.commit_index("chore: submodule")

        with self.assertRaises(ValueError) as caught:
            git_sync.list_remote_files(str(self.repo), commit, "files")

        self.assertIn("files/vendor", str(caught.exception))

    def test_rejects_a_symbolic_link_at_the_requested_directory(self):
        from workbench.bridge import git_sync

        self.write("target/real.md", "x\n")
        self.commit("chore: target")
        self.stage_entry("120000", self.blob_of("target/real.md"), "files")
        commit = self.commit_index("chore: linked directory")

        with self.assertRaises(ValueError):
            git_sync.list_remote_files(str(self.repo), commit, "files")


if __name__ == "__main__":
    unittest.main()
