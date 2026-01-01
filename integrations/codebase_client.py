"""
Codebase Analysis Client
Analyze code repositories for patterns, dependencies, and structure
"""

import os
import re
import json
import subprocess
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
from collections import defaultdict
import fnmatch


class CodebaseClient:
    """Client for analyzing codebases and repositories."""

    def __init__(self, repo_path: str = "."):
        """
        Initialize Codebase client.

        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = self._load_gitignore()

    def _load_gitignore(self) -> List[str]:
        """Load patterns from .gitignore"""
        patterns = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            '*.pyc', '*.pyo', '.eggs', '*.egg-info', 'dist', 'build',
            '.pytest_cache', '.mypy_cache', '.tox', 'coverage.xml',
            '*.log', '.DS_Store', 'Thumbs.db'
        ]

        gitignore_path = self.repo_path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)

        return patterns

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return True
            if fnmatch.fnmatch(str(path), pattern):
                return True
        return False

    # File Operations
    def list_files(
        self,
        extensions: List[str] = None,
        max_depth: int = None,
        include_hidden: bool = False
    ) -> List[str]:
        """
        List all files in the repository.

        Args:
            extensions: Filter by file extensions (e.g., ['.py', '.js'])
            max_depth: Maximum directory depth
            include_hidden: Include hidden files

        Returns:
            List of file paths relative to repo root
        """
        files = []

        for root, dirs, filenames in os.walk(self.repo_path):
            # Calculate depth
            depth = len(Path(root).relative_to(self.repo_path).parts)
            if max_depth and depth > max_depth:
                dirs.clear()
                continue

            # Filter directories
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in filenames:
                if not include_hidden and filename.startswith('.'):
                    continue

                file_path = Path(root) / filename
                if self._should_ignore(file_path):
                    continue

                if extensions:
                    if not any(filename.endswith(ext) for ext in extensions):
                        continue

                rel_path = file_path.relative_to(self.repo_path)
                files.append(str(rel_path))

        return sorted(files)

    def read_file(self, file_path: str, max_lines: int = 1000) -> str:
        """Read file contents"""
        full_path = self.repo_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[:max_lines]
            return ''.join(lines)

    def search_files(
        self,
        pattern: str,
        file_patterns: List[str] = None,
        case_sensitive: bool = False,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search for pattern in files.

        Args:
            pattern: Regex pattern to search
            file_patterns: Glob patterns for files to search
            case_sensitive: Case sensitive search
            max_results: Maximum number of results

        Returns:
            List of matches with file, line number, and content
        """
        matches = []
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        files = self.list_files()
        if file_patterns:
            filtered_files = []
            for fp in file_patterns:
                filtered_files.extend(
                    f for f in files if fnmatch.fnmatch(f, fp)
                )
            files = list(set(filtered_files))

        for file_path in files:
            if len(matches) >= max_results:
                break

            try:
                content = self.read_file(file_path)
                for i, line in enumerate(content.split('\n'), 1):
                    if regex.search(line):
                        matches.append({
                            'file': file_path,
                            'line': i,
                            'content': line.strip()[:200]
                        })
                        if len(matches) >= max_results:
                            break
            except Exception:
                continue

        return matches

    # Structure Analysis
    def get_structure(self, max_depth: int = 3) -> Dict:
        """
        Get repository structure as a tree.

        Args:
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing directory structure
        """
        def build_tree(path: Path, depth: int = 0) -> Dict:
            if depth > max_depth:
                return {}

            tree = {}
            try:
                for item in sorted(path.iterdir()):
                    if self._should_ignore(item):
                        continue

                    if item.is_dir():
                        tree[item.name + '/'] = build_tree(item, depth + 1)
                    else:
                        tree[item.name] = item.stat().st_size
            except PermissionError:
                pass

            return tree

        return build_tree(self.repo_path)

    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about files in the repository"""
        stats = {
            'total_files': 0,
            'total_lines': 0,
            'by_extension': defaultdict(lambda: {'files': 0, 'lines': 0}),
            'largest_files': [],
            'recently_modified': []
        }

        files_with_size = []
        files_with_mtime = []

        for file_path in self.list_files():
            try:
                full_path = self.repo_path / file_path
                size = full_path.stat().st_size
                mtime = full_path.stat().st_mtime

                ext = Path(file_path).suffix or 'no_extension'
                lines = sum(1 for _ in open(full_path, 'rb'))

                stats['total_files'] += 1
                stats['total_lines'] += lines
                stats['by_extension'][ext]['files'] += 1
                stats['by_extension'][ext]['lines'] += lines

                files_with_size.append((file_path, size))
                files_with_mtime.append((file_path, mtime))
            except Exception:
                continue

        # Top 10 largest files
        files_with_size.sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = [
            {'file': f, 'size': s}
            for f, s in files_with_size[:10]
        ]

        # Top 10 recently modified
        files_with_mtime.sort(key=lambda x: x[1], reverse=True)
        from datetime import datetime
        stats['recently_modified'] = [
            {'file': f, 'modified': datetime.fromtimestamp(m).isoformat()}
            for f, m in files_with_mtime[:10]
        ]

        stats['by_extension'] = dict(stats['by_extension'])

        return stats

    # Dependency Analysis
    def get_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        deps = {
            'python': self._get_python_deps(),
            'nodejs': self._get_node_deps(),
            'docker': self._get_docker_deps(),
            'kubernetes': self._get_k8s_resources()
        }
        return {k: v for k, v in deps.items() if v}

    def _get_python_deps(self) -> Dict:
        """Get Python dependencies"""
        deps = {}

        # requirements.txt
        req_file = self.repo_path / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                deps['requirements.txt'] = [
                    line.strip() for line in f
                    if line.strip() and not line.startswith('#')
                ]

        # pyproject.toml
        pyproject = self.repo_path / 'pyproject.toml'
        if pyproject.exists():
            deps['pyproject.toml'] = 'present'

        # setup.py
        setup = self.repo_path / 'setup.py'
        if setup.exists():
            deps['setup.py'] = 'present'

        return deps

    def _get_node_deps(self) -> Dict:
        """Get Node.js dependencies"""
        deps = {}

        pkg_file = self.repo_path / 'package.json'
        if pkg_file.exists():
            with open(pkg_file, 'r') as f:
                data = json.load(f)
                deps['dependencies'] = list(data.get('dependencies', {}).keys())
                deps['devDependencies'] = list(data.get('devDependencies', {}).keys())

        return deps

    def _get_docker_deps(self) -> Dict:
        """Get Docker-related files"""
        deps = {}

        dockerfile = self.repo_path / 'Dockerfile'
        if dockerfile.exists():
            with open(dockerfile, 'r') as f:
                content = f.read()
                from_match = re.search(r'^FROM\s+(.+)$', content, re.MULTILINE)
                if from_match:
                    deps['base_image'] = from_match.group(1)

        compose_file = self.repo_path / 'docker-compose.yml'
        if not compose_file.exists():
            compose_file = self.repo_path / 'docker-compose.yaml'

        if compose_file.exists():
            deps['docker_compose'] = 'present'

        return deps

    def _get_k8s_resources(self) -> List[Dict]:
        """Find Kubernetes manifests"""
        resources = []

        for file_path in self.list_files(extensions=['.yaml', '.yml']):
            try:
                content = self.read_file(file_path)
                if 'apiVersion:' in content and 'kind:' in content:
                    kind_match = re.search(r'^kind:\s*(.+)$', content, re.MULTILINE)
                    if kind_match:
                        resources.append({
                            'file': file_path,
                            'kind': kind_match.group(1).strip()
                        })
            except Exception:
                continue

        return resources

    # Git Operations
    def get_git_info(self) -> Dict:
        """Get Git repository information"""
        info = {}

        try:
            # Current branch
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['branch'] = result.stdout.strip()

            # Remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['remote'] = result.stdout.strip()

            # Recent commits
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['recent_commits'] = result.stdout.strip().split('\n')

            # Uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                changes = result.stdout.strip().split('\n')
                info['uncommitted_changes'] = len([c for c in changes if c])

        except Exception as e:
            info['error'] = str(e)

        return info

    def get_git_diff(self, base: str = 'HEAD~1') -> str:
        """Get git diff"""
        try:
            result = subprocess.run(
                ['git', 'diff', base],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error: {e}"

    # Code Quality
    def find_todos(self) -> List[Dict]:
        """Find TODO, FIXME, XXX comments"""
        return self.search_files(
            r'\b(TODO|FIXME|XXX|HACK|BUG)\b.*$',
            file_patterns=['*.py', '*.js', '*.ts', '*.java', '*.go', '*.rb']
        )

    def find_security_issues(self) -> List[Dict]:
        """Find potential security issues"""
        patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'(AWS_ACCESS_KEY|AWS_SECRET)',
            r'eval\s*\(',
            r'exec\s*\(',
            r'subprocess\.call\s*\(\s*shell\s*=\s*True',
        ]

        issues = []
        for pattern in patterns:
            matches = self.search_files(pattern, max_results=20)
            for match in matches:
                match['pattern'] = pattern
                issues.append(match)

        return issues

    # Summary
    def get_summary(self) -> Dict:
        """Get comprehensive repository summary"""
        return {
            'path': str(self.repo_path),
            'git': self.get_git_info(),
            'stats': self.get_file_stats(),
            'dependencies': self.get_dependencies(),
            'structure': self.get_structure(max_depth=2),
            'todos': len(self.find_todos()),
            'potential_security_issues': len(self.find_security_issues())
        }
