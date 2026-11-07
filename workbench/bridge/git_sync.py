"""System Git transport for the course file exchange.

This module moves bytes and reports what the repository and the remote actually
contain. It never merges course content, never touches SQLite and never resets,
checks out or force-pushes anything: the coordinator compares the file set that
`fetch_remote`/`read_remote_files` expose and composes the receipt. Every Git
call is an argument array with an explicit working directory, so no URL, branch
or course path is ever interpreted by a shell.
"""

import os
import posixpath
import re
import subprocess

from workbench.bridge.conversation_providers import hidden_launch_kwargs

DEFAULT_MESSAGE = 'Sync managed course files'

# Remote bytes land in a private ref namespace so comparing never rewrites the
# user's branches, index or working tree.
REMOTE_REF_NAMESPACE = 'refs/lessonkit/remote'

_USERINFO = re.compile(r'(?<=://)[^/\s@]+@')
_QUERY_SECRET = re.compile(r'([?&](?:token|access_token|key|api_key|password|signature)=)[^&\s]+', re.I)


def sanitize(text):
    """Remove credentials that Git may echo from a remote URL."""
    return _QUERY_SECRET.sub(r'\1***', _USERINFO.sub('***@', text or ''))


def _git(repo, *args, check=True):
    completed = subprocess.run(
        ['git', '--literal-pathspecs', *args],
        cwd=str(repo),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dict(os.environ, GIT_TERMINAL_PROMPT='0'),
        **hidden_launch_kwargs(),
    )
    if check and completed.returncode:
        raise RuntimeError(sanitize(f"git {args[0]} failed: {_failure_text(completed)}"))
    return completed


def _failure_text(completed):
    for stream in (completed.stderr, completed.stdout):
        text = stream.decode('utf-8', 'replace').strip()
        if text:
            return sanitize(text)
    return f'exit code {completed.returncode}'


def _text(completed):
    return completed.stdout.decode('utf-8', 'replace').strip()


def _records(completed):
    return [item for item in completed.stdout.decode('utf-8', 'replace').split('\0') if item]


def _repository_root(repo):
    """Resolve the working-tree root and refuse anything else.

    Managed paths are relative to this directory, so a subdirectory would make
    `git add` and the exchange disagree about what a path means.
    """
    candidate = os.path.realpath(str(repo))
    if not os.path.isdir(candidate):
        raise ValueError(f'repository directory does not exist: {repo}')
    located = _git(candidate, 'rev-parse', '--show-toplevel', check=False)
    if located.returncode:
        raise ValueError(sanitize(f'not a Git repository: {repo}'))
    root = os.path.realpath(_text(located))
    if os.path.normcase(root) != os.path.normcase(candidate):
        raise ValueError(f'repo must be the working-tree root, not {repo}')
    return root


def _branch(branch):
    if (
        not isinstance(branch, str)
        or not branch
        or branch.startswith('-')
        or any(character.isspace() or ord(character) < 32 for character in branch)
        or any(marker in branch for marker in ('..', ':', '\\'))
        or branch.startswith('/')
        or branch.endswith('/')
    ):
        raise ValueError(f'invalid branch name: {branch!r}')
    return branch


def _remote_name(remote):
    if (
        not isinstance(remote, str)
        or not remote
        or remote.startswith('-')
        or any(character.isspace() or ord(character) < 32 for character in remote)
    ):
        raise ValueError(f'invalid remote name: {remote!r}')
    return remote


def _managed_paths(root, paths):
    """Validate explicit relative paths and normalize them for Git."""
    if isinstance(paths, str) or not paths:
        raise ValueError('managed_paths must be a list of relative file paths')
    validated = []
    for raw in paths:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError('managed path must be a non-empty string')
        relative = posixpath.normpath(raw.replace('\\', '/'))
        if (
            posixpath.isabs(relative)
            or relative in ('.', '..')
            or relative.startswith('../')
            or re.match(r'^[A-Za-z]:', raw)
        ):
            raise ValueError(f'managed path escapes repository: {raw!r}')
        if any(part.lower().rstrip(' .') == '.git' for part in relative.split('/')):
            raise ValueError(f'managed path targets Git metadata: {raw!r}')
        if ':' in relative or any(part != part.rstrip(' .') for part in relative.split('/')):
            raise ValueError(f'managed path has an ambiguous Windows spelling: {raw!r}')
        target = os.path.realpath(os.path.join(root, *relative.split('/')))
        try:
            inside = os.path.normcase(os.path.commonpath(
                [os.path.normcase(root), os.path.normcase(target)])) == os.path.normcase(root)
        except ValueError:
            inside = False
        if not inside:
            raise ValueError(f'managed path escapes repository: {raw!r}')
        if os.path.islink(target):
            raise ValueError(f'managed path is a symbolic link: {raw!r}')
        if os.path.isdir(target):
            raise ValueError(f'managed path is a directory: {raw!r}')
        if relative not in validated:
            validated.append(relative)
    return validated


def _revision(root, ref):
    completed = _git(root, 'rev-parse', '--verify', '--quiet', ref, check=False)
    return _text(completed) if completed.returncode == 0 and _text(completed) else None


def _current_branch(root):
    completed = _git(root, 'symbolic-ref', '--short', '--quiet', 'HEAD', check=False)
    return _text(completed) if completed.returncode == 0 and _text(completed) else None


def _status(root):
    staged, modified, untracked = [], [], []
    listing = _git(
        root, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--no-renames'
    )
    for record in _records(listing):
        if len(record) < 4:
            continue
        code, path = record[:2], record[3:]
        if code == '??':
            untracked.append(path)
            continue
        if code[0] not in ' ?':
            staged.append(path)
        if code[1] not in ' ?':
            modified.append(path)
    return {'staged': staged, 'modified': modified, 'untracked': untracked}


def _staged_paths(root):
    if _revision(root, 'HEAD'):
        listing = _git(root, 'diff', '--cached', '--name-only', '-z', '--no-renames')
    else:
        listing = _git(root, 'ls-files', '--cached', '-z')
    return _records(listing)


def _remote_commit(root, remote, branch):
    listing = _git(root, 'ls-remote', remote, f'refs/heads/{branch}', check=False)
    if listing.returncode:
        return None, _failure_text(listing)
    for line in listing.stdout.decode('utf-8', 'replace').splitlines():
        commit, _, ref = line.partition('\t')
        if ref.strip() == f'refs/heads/{branch}':
            return commit.strip(), None
    return None, None


def inspect_repository(repo, branch, remote='origin'):
    """Report the local branch, worktree and configured remote without mutating them."""
    root = _repository_root(repo)
    branch, remote = _branch(branch), _remote_name(remote)
    head_commit = _revision(root, 'HEAD')
    head_branch = _current_branch(root)
    branch_commit = _revision(root, f'refs/heads/{branch}')
    status = _status(root)
    remote_url = _git(root, 'config', '--get', f'remote.{remote}.url', check=False)
    return {
        'repo': root,
        'branch': branch,
        'remote': remote,
        'head_commit': head_commit,
        'head_branch': head_branch,
        'branch_exists': branch_commit is not None,
        'branch_commit': branch_commit,
        'branch_checked_out': head_branch == branch,
        'repository_clean': not (status['staged'] or status['modified'] or status['untracked']),
        'staged_paths': status['staged'],
        'modified_paths': status['modified'],
        'untracked_paths': status['untracked'],
        'remote_url': sanitize(_text(remote_url)) or None,
        'tracking_commit': _revision(root, f'refs/remotes/{remote}/{branch}'),
    }


def fetch_remote(repo, branch, remote='origin'):
    """Fetch the configured remote branch into a private ref for comparison.

    The fetch refspec is forced only inside `refs/lessonkit/remote/`; the user's
    branches, index and working tree stay exactly as they were.
    """
    root = _repository_root(repo)
    branch, remote = _branch(branch), _remote_name(remote)
    ref = f'{REMOTE_REF_NAMESPACE}/{branch}'
    _git(root, 'fetch', '--quiet', '--no-tags', '--no-write-fetch-head',
         remote, f'+refs/heads/{branch}:{ref}')
    commit = _revision(root, ref)
    if not commit:
        raise RuntimeError(sanitize(f'fetched {ref} has no commit'))
    return {'repo': root, 'branch': branch, 'remote': remote, 'ref': ref, 'commit': commit}


def read_remote_files(repo, commit, paths):
    """Read managed files at a fetched commit as raw bytes."""
    root = _repository_root(repo)
    if not isinstance(commit, str) or not commit or commit.startswith('-') or any(
        character.isspace() for character in commit
    ):
        raise ValueError(f'invalid commit: {commit!r}')
    resolved = _git(root, 'rev-parse', '--verify', '--quiet', f'{commit}^{{commit}}',
                    check=False)
    if resolved.returncode:
        raise ValueError(sanitize(f'unknown commit: {commit}'))
    resolved_commit = _text(resolved)
    wanted = _managed_paths(root, paths)
    listing = _git(root, 'ls-tree', '-z', resolved_commit, '--', *wanted)
    entries = {}
    for record in _records(listing):
        meta, _, name = record.partition('\t')
        mode, kind, sha = meta.split(' ')
        entries[name] = (mode, kind, sha)
    files, missing = {}, []
    for path in wanted:
        entry = entries.get(path)
        if entry is None:
            if any(name.startswith(f'{path}/') for name in entries):
                raise ValueError(f'managed path is not a file: {path!r}')
            missing.append(path)
            continue
        mode, kind, sha = entry
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError(f'managed path is not a regular file: {path!r}')
        files[path] = _git(root, 'cat-file', 'blob', sha).stdout
    return {'commit': resolved_commit, 'files': files, 'missing': missing}


def publish(repo, branch, managed_paths, remote='origin', message=DEFAULT_MESSAGE):
    """Commit the managed paths on the checked-out branch and push them normally.

    Unrelated staged files are refused instead of committed, unrelated worktree
    changes stay untouched, an unchanged file set produces no commit, and a
    rejected push is reported without forcing or discarding the local commit.
    """
    root = _repository_root(repo)
    branch, remote = _branch(branch), _remote_name(remote)
    paths = _managed_paths(root, managed_paths)
    if not isinstance(message, str) or not message.strip():
        raise ValueError('commit message must be a non-empty string')
    current = _current_branch(root)
    if current != branch:
        raise ValueError(sanitize(
            f'configured branch {branch!r} is not checked out (HEAD is {current or "detached"})'))
    unrelated = [path for path in _staged_paths(root) if path not in paths]
    if unrelated:
        raise ValueError(sanitize(
            'unrelated staged files must be committed or unstaged first: ' + ', '.join(unrelated)))

    previous_commit = _revision(root, 'HEAD')
    _git(root, 'add', '-A', '--', *paths)
    changed = _staged_paths(root)
    created_commit = None
    if changed:
        _git(root, 'commit', '--quiet', '-m', message, '--', *paths)
        created_commit = _revision(root, 'HEAD')
    local = {
        'status': 'committed' if created_commit else 'unchanged',
        'commit': _revision(root, 'HEAD'),
        'created_commit': created_commit,
        'previous_commit': previous_commit,
        'changed_paths': changed if created_commit else [],
    }

    refspec = f'refs/heads/{branch}:refs/heads/{branch}'
    if not local['commit']:
        return {
            'repo': root, 'branch': branch, 'remote_name': remote, 'managed_paths': paths,
            'local': local,
            'remote': {'status': 'failed', 'commit': None,
                       'reason': 'no local commit to publish'},
        }
    before, _ = _remote_commit(root, remote, branch)
    push = _git(root, 'push', '--quiet', remote, refspec, check=False)
    after, lookup_error = _remote_commit(root, remote, branch)
    if push.returncode:
        remote_state = {'status': 'failed', 'commit': after,
                        'reason': sanitize(_failure_text(push))}
    elif after != local['commit']:
        remote_state = {'status': 'failed', 'commit': after,
                        'reason': lookup_error or
                        f'remote {branch} is {after or "absent"}, expected {local["commit"]}'}
    else:
        remote_state = {'status': 'published' if before != after else 'unchanged',
                        'commit': after, 'reason': None}
    return {
        'repo': root, 'branch': branch, 'remote_name': remote, 'managed_paths': paths,
        'local': local, 'remote': remote_state,
    }
