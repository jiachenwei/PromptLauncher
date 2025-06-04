import os
import paramiko
import logging
import posixpath
import threading
from PyQt6.QtCore import QTimer
from datetime import datetime

# 配置日志输出
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
paramiko_logger = logging.getLogger('paramiko')
paramiko_logger.setLevel(logging.DEBUG)
paramiko_logger.addHandler(handler)

class SshBackupManager:
    """
    定时通过 SSH/SFTP 备份本地文件到远程服务器。
    配置示例 cfg: {
        "host": "example.com",
        "port": 22,
        "user": "username",
        "remote_path": "/remote/dir",
        "key_path": "C:/path/to/key.pem",
        "interval": 60  # 备份间隔(秒)
    }
    """
    def __init__(self, cfg: dict, local_file: str, window=None):
        self.cfg = cfg
        self.local_file = local_file
        self.window = window
        interval = int(cfg.get("interval", 10))
        logger.debug(f"SSHBackupManager init: interval={interval} minutes, local_file={local_file}, cfg={cfg}")
        self.timer = QTimer()
        # 定时触发备份动作，但在后台线程执行，避免阻塞 UI
        self.timer.timeout.connect(self._start_backup_thread)
        # 将秒转换为毫秒
        self.timer.start(interval * 1000)
        # 立即异步执行一次备份
        self._start_backup_thread()

    def backup(self):
        timestamp = datetime.now()
        logger.debug(f"Starting SSH backup at {timestamp}")
        host = self.cfg.get("host")
        port = int(self.cfg.get("port", 22))
        user = self.cfg.get("user")
        remote_path = self.cfg.get("remote_path")
        key_path = self.cfg.get("key_path")
        if not all([host, user, remote_path, key_path]):
            logger.warning("SSH backup skipped: incomplete configuration")
            return  # 配置不全时跳过
        logger.debug(f"Connecting to {host}:{port} as {user}, remote_path={remote_path}")
        success = False
        transport = None
        sftp = None
        try:
            logger.debug(f"Loading private key from {key_path}")
            key = paramiko.RSAKey.from_private_key_file(key_path)
            logger.debug("Creating SFTP transport")
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, pkey=key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            logger.debug("Ensuring remote directory exists")
            self._ensure_remote_dir(sftp, remote_path)
            filename = os.path.basename(self.local_file)
            remote_file = posixpath.join(remote_path, filename)
            logger.debug(f"Uploading {self.local_file} to {remote_file}")
            sftp.put(self.local_file, remote_file)
            logger.info("SSH backup successful")
            success = True
        except Exception as e:
            logger.error(f"SSH backup error: {e}", exc_info=True)
        finally:
            if sftp:
                try:
                    sftp.close()
                except Exception:
                    logger.debug("Error closing sftp", exc_info=True)
            if transport:
                try:
                    transport.close()
                except Exception:
                    logger.debug("Error closing transport", exc_info=True)
            # 通知 GUI 同步状态
            if self.window:
                self.window.update_sync_status(timestamp, success)
    
    def _start_backup_thread(self):
        """在后台线程中执行备份，避免阻塞 UI 线程"""
        threading.Thread(target=self.backup, daemon=True).start()
    
    def _ensure_remote_dir(self, sftp, remote_directory: str):
        """
        确保远程目录存在，不存在时递归创建。
        """
        dirs = []
        current = remote_directory.rstrip('/')
        # 收集需要创建的目录列表
        while True:
            try:
                sftp.stat(current)
                break
            except IOError:
                dirs.append(current)
                parent = os.path.dirname(current)
                if not parent or parent == current:
                    break
                current = parent
        # 按层级创建目录
        for dir_path in reversed(dirs):
            try:
                sftp.mkdir(dir_path)
            except IOError:
                pass