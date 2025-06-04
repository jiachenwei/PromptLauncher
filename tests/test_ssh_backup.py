import types
import sys

from pathlib import Path
import importlib.util

# Provide stub for paramiko so ssh_backup.py can be loaded without the package
sys.modules.setdefault("paramiko", types.ModuleType("paramiko"))

# Create a minimal package to satisfy relative imports without loading PyQt6
pkg = types.ModuleType("promptlauncher")
pkg.__path__ = [str(Path(__file__).parents[1] / "promptlauncher")]
sys.modules["promptlauncher"] = pkg

# Stub out PyQt6 modules used in ssh_backup
for name in ["PyQt6", "PyQt6.QtCore"]:
    sys.modules.setdefault(name, types.ModuleType(name))

# Provide dummy QTimer attribute
sys.modules["PyQt6.QtCore"].QTimer = object

# Load required modules manually
for mod_name in ["logging_config"]:
    mpath = Path(__file__).parents[1] / "promptlauncher" / f"{mod_name}.py"
    spec = importlib.util.spec_from_file_location(f"promptlauncher.{mod_name}", mpath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

# Load ssh_backup module
file_path = Path(__file__).parents[1] / "promptlauncher" / "ssh_backup.py"
spec = importlib.util.spec_from_file_location("promptlauncher.ssh_backup", file_path)
ssh_backup = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ssh_backup
spec.loader.exec_module(ssh_backup)
SshBackupManager = ssh_backup.SshBackupManager

class DummySFTP:
    def __init__(self, existing=None):
        self.paths = set(existing or [])
        self.mkdir_calls = []
    def stat(self, path):
        if path not in self.paths:
            raise IOError('not found')
    def mkdir(self, path):
        self.paths.add(path)
        self.mkdir_calls.append(path)


def call_ensure(manager, sftp, path):
    # use __new__ to avoid QTimer setup in __init__
    if isinstance(manager, type):
        manager = manager.__new__(manager)
    SshBackupManager._ensure_remote_dir(manager, sftp, path)


def test_ensure_creates_missing_dirs():
    sftp = DummySFTP(existing={'/existing'})
    call_ensure(SshBackupManager, sftp, '/existing/sub/dir')
    assert sftp.mkdir_calls == ['/existing/sub', '/existing/sub/dir']


def test_ensure_no_action_when_exists():
    sftp = DummySFTP(existing={'/existing/sub/dir'})
    call_ensure(SshBackupManager, sftp, '/existing/sub/dir')
    assert sftp.mkdir_calls == []
