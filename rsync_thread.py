# rsync_thread.py

from PySide6.QtCore import QThread, Signal
import subprocess

class RsyncThread(QThread):
    progress_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, rsync_command):
        super().__init__()
        self.rsync_command = rsync_command

    def run(self):
        try:
            process = subprocess.Popen(
                self.rsync_command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True
            )
            while True:
                output = process.stdout.readline()
                if output:
                    self.progress_signal.emit(output.strip())
                elif process.poll() is not None:
                    break

            stderr = process.stderr.read()
            if process.returncode == 0:
                self.finished_signal.emit(True)
            else:
                self.error_signal.emit(stderr)
                self.finished_signal.emit(False)
        except Exception as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(False)
