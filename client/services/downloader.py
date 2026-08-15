
"""
GRÁFICOS VICTORTRUCKS - Streaming Download Worker
Supports resumable downloads via HTTP Range, 10GB+ files, SHA-256 verification.
"""
import os
import time
import hashlib
import requests
from client.ui.qt_compat import QThread, Signal


class DownloadWorker(QThread):
    progress_signal = Signal(int, int, int, float, float)  # mod_id, downloaded_bytes, total_bytes, percentage, speed_mbps
    completed_signal = Signal(int, str, str, bool)          # mod_id, file_path, sha256_hash, sha256_verified
    error_signal = Signal(int, str)                         # mod_id, error_message

    # 1 MB chunks for optimal throughput on large files (10GB+)
    CHUNK_SIZE = 1024 * 1024
    # Minimum interval between progress signal emissions (ms)
    PROGRESS_INTERVAL = 0.5

    def __init__(self, mod_id, download_url, save_directory, expected_sha256, filename, total_size_bytes, auth_token=None):
        super().__init__()
        self.mod_id = mod_id
        self.download_url = download_url
        self.save_directory = save_directory
        self.expected_sha256 = expected_sha256
        self.filename = filename
        self.total_size_bytes = total_size_bytes
        self.auth_token = auth_token
        self.target_path = os.path.join(save_directory, filename)
        self.temp_path = self.target_path + ".download"

        # Session resume state
        self.is_paused = False
        self.is_cancelled = False
        self.is_resume = False
        self.downloaded_bytes = 0

    # ------------------------------------------------------------------
    # Control methods
    # ------------------------------------------------------------------
    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
        self.is_resume = True
        if not self.isRunning():
            self.start()

    def cancel(self):
        self.is_cancelled = True
        self.is_paused = False

    # ------------------------------------------------------------------
    # Main download logic
    # ------------------------------------------------------------------
    def run(self):
        os.makedirs(self.save_directory, exist_ok=True)
        downloaded_bytes = 0

        # Check existing partial download for HTTP Range resumption
        if os.path.exists(self.temp_path):
            downloaded_bytes = os.path.getsize(self.temp_path)
            self.downloaded_bytes = downloaded_bytes

        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if downloaded_bytes > 0:
            headers["Range"] = f"bytes={downloaded_bytes}-"

        # Handle Google Drive confirmation page for large files
        download_url = self.download_url
        if 'drive.google.com' in download_url or 'drive.usercontent.google.com' in download_url:
            import re
            file_id_match = re.search(r'[?&]id=([^&]+)', download_url)
            if not file_id_match:
                file_id_match = re.search(r'/file/d/([^/]+)', download_url)
            if file_id_match:
                file_id = file_id_match.group(1)
                download_url = f'https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t&authuser=0'
        try:
            resp = requests.get(download_url, headers=headers, stream=True, timeout=60, allow_redirects=True)

            # If CDN/external storage rejects custom Bearer auth header, retry without Authorization
            if resp.status_code in (400, 403) and self.auth_token and "Authorization" in headers:
                cdn_headers = {k: v for k, v in headers.items() if k != "Authorization"}
                resp = requests.get(download_url, headers=cdn_headers, stream=True, timeout=60)

            # If server doesn't support range, restart from beginning
            if resp.status_code == 416:
                # Range not satisfiable - file may have changed on server
                self.delete_temp_file()
                downloaded_bytes = 0
                no_range_headers = {k: v for k, v in headers.items() if k != "Range"}
                resp = requests.get(download_url, headers=no_range_headers, stream=True, timeout=60)
            elif resp.status_code not in (200, 206):
                # Other status - try without Range header
                downloaded_bytes = 0
                no_range_headers = {k: v for k, v in headers.items() if k != "Range"}
                resp = requests.get(download_url, headers=no_range_headers, stream=True, timeout=60)

            total_bytes = downloaded_bytes
            if "Content-Length" in resp.headers:
                content_length = int(resp.headers.get("Content-Length", 0))
                if resp.status_code == 206:
                    # Partial content: Content-Length is remaining bytes
                    total_bytes = downloaded_bytes + content_length
                else:
                    # Full content: Content-Length is whole file
                    total_bytes = content_length
            else:
                total_bytes = max(self.total_size_bytes, downloaded_bytes)

            # Determine write mode
            mode = "ab" if downloaded_bytes > 0 and resp.status_code == 206 else "wb"
            if resp.status_code == 200 and downloaded_bytes > 0:
                # Server returned full file; restart
                mode = "wb"
                downloaded_bytes = 0

            # Speed calculation with sliding window
            speed_window_start = time.time()
            speed_window_bytes = 0
            last_progress_time = 0

            with open(self.temp_path, mode) as f:
                for chunk in resp.iter_content(chunk_size=self.CHUNK_SIZE):
                    if self.is_cancelled:
                        # Don't call f.close() — 'with' handles it
                        self.delete_temp_file()
                        self.error_signal.emit(self.mod_id, "Descarga cancelada por el usuario")
                        return

                    if self.is_paused:
                        # Don't call f.close() — 'with' handles it
                        self.error_signal.emit(self.mod_id, "PAUSED")
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        speed_window_bytes += len(chunk)

                        now = time.time()
                        elapsed_since_window = now - speed_window_start
                        elapsed_since_progress = now - last_progress_time

                        # Throttle progress signals to avoid UI overhead
                        if elapsed_since_progress >= self.PROGRESS_INTERVAL:
                            if elapsed_since_window > 0:
                                speed_mbps = (speed_window_bytes / (1024 * 1024)) / elapsed_since_window
                            else:
                                speed_mbps = 0.0
                            pct = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
                            self.progress_signal.emit(self.mod_id, downloaded_bytes, total_bytes, pct, speed_mbps)
                            last_progress_time = now

                            # Reset speed window every 2 seconds for smoother readings
                            if elapsed_since_window >= 2.0:
                                speed_window_start = now
                                speed_window_bytes = 0

            # Emit final 100% progress
            pct = 100.0 if total_bytes > 0 else 0
            self.progress_signal.emit(self.mod_id, downloaded_bytes, total_bytes, pct, 0.0)

            # Move temp file to final target path
            if os.path.exists(self.target_path):
                os.remove(self.target_path)
            os.rename(self.temp_path, self.target_path)
            # Ocultar archivo en Windows
            try:
                import subprocess
                subprocess.run(["attrib", "+h", self.target_path], check=False)
            except Exception:
                pass

            # SHA-256 Checksum Verification
            verified = self.verify_sha256(self.target_path, self.expected_sha256)
            self.completed_signal.emit(self.mod_id, self.target_path, self.expected_sha256, verified)

        except requests.exceptions.RequestException as e:
            self.error_signal.emit(self.mod_id, f"Error de red durante la descarga: {str(e)}")
        except Exception as e:
            self.error_signal.emit(self.mod_id, f"Error durante la descarga: {str(e)}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def delete_temp_file(self):
        try:
            if os.path.exists(self.temp_path):
                os.remove(self.temp_path)
        except Exception:
            pass

    def verify_sha256(self, filepath, expected_hash):
        if not expected_hash:
            return True
        try:
            hasher = hashlib.sha256()
            with open(filepath, "rb") as f:
                while chunk := f.read(self.CHUNK_SIZE):
                    hasher.update(chunk)
            calculated = hasher.hexdigest().lower()
            return calculated == expected_hash.lower()
        except Exception:
            return False

    def get_downloaded_bytes(self):
        """Return current downloaded bytes for UI."""
        if self.downloaded_bytes > 0:
            return self.downloaded_bytes
        if os.path.exists(self.temp_path):
            return os.path.getsize(self.temp_path)
        return 0