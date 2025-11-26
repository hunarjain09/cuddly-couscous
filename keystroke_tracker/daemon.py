"""
Daemon/background process utilities
Allows keystroke tracker to run in the background
"""

import os
import sys
import time
import signal
import atexit
from pathlib import Path


class Daemon:
    """
    A generic daemon class for running processes in the background.

    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        """
        Initialize daemon

        Args:
            pidfile: Path to PID file
            stdin: stdin redirection
            stdout: stdout redirection
            stderr: stderr redirection
        """
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        Daemonize the process using Unix double-fork
        """
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"fork #1 failed: {e}\n")
            sys.exit(1)

        # Decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"fork #2 failed: {e}\n")
            sys.exit(1)

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write(f"{pid}\n")

    def delpid(self):
        """Remove PID file"""
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        """Start the daemon"""
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            # Check if process is actually running
            try:
                os.kill(pid, 0)
                message = f"Daemon already running (PID {pid})\n"
                sys.stderr.write(message)
                sys.exit(1)
            except OSError:
                # PID file exists but process is dead, remove stale PID file
                os.remove(self.pidfile)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """Stop the daemon"""
        # Get the pid from the pidfile
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = "Daemon not running (no PID file found)\n"
            sys.stderr.write(message)
            return

        # Try killing the daemon process
        try:
            # First try graceful shutdown
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)

            # Check if still running
            try:
                os.kill(pid, 0)
                # Still running, force kill
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.3)
            except OSError:
                pass

        except OSError as err:
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            sys.stderr.write(f"Failed to stop daemon: {err}\n")
            sys.exit(1)

        # Remove PID file
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

        print(f"Daemon stopped (PID {pid})")

    def restart(self):
        """Restart the daemon"""
        self.stop()
        time.sleep(1)
        self.start()

    def status(self):
        """Check daemon status"""
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            print("Daemon is not running (no PID file)")
            return False

        # Check if process is actually running
        try:
            os.kill(pid, 0)
            print(f"Daemon is running (PID {pid})")
            return True
        except OSError:
            print("Daemon is not running (stale PID file)")
            os.remove(self.pidfile)
            return False

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been daemonized.
        """
        raise NotImplementedError("Must override run() method")


class KeystrokeTrackerDaemon(Daemon):
    """Daemon for running keystroke tracker in background"""

    def __init__(self, pidfile, data_file, logfile=None):
        """
        Initialize tracker daemon

        Args:
            pidfile: Path to PID file
            data_file: Path to keystroke data file
            logfile: Path to log file (optional)
        """
        self.data_file = data_file

        # Set up logging
        if logfile is None:
            logfile = 'data/tracker.log'
        self.logfile = logfile

        # Ensure log directory exists
        os.makedirs(os.path.dirname(logfile), exist_ok=True)

        # Initialize daemon with log output
        super().__init__(pidfile, stdout=logfile, stderr=logfile)

    def run(self):
        """Run the keystroke tracker"""
        from keystroke_tracker.tracker import KeystrokeTracker

        # Log startup
        with open(self.logfile, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Keystroke Tracker Daemon Started\n")
            f.write(f"PID: {os.getpid()}\n")
            f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data file: {self.data_file}\n")
            f.write(f"{'='*60}\n\n")

        # Create and start tracker
        tracker = KeystrokeTracker(data_file=self.data_file)

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            with open(self.logfile, 'a') as f:
                f.write(f"\nReceived signal {signum}, stopping tracker...\n")
            tracker.stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Start tracking
        try:
            tracker.start()
        except Exception as e:
            with open(self.logfile, 'a') as f:
                f.write(f"Error: {e}\n")
            raise
