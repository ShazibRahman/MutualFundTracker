import logging
import os

import psutil


class LockError(Exception):
    pass


def check_pid_exists(pid):
    """
    Check if a process with the given PID exists.

    Args:
        pid (int): The PID of the process to check.

    Returns:
        bool: True if a process with the given PID exists, False otherwise.
    """
    return psutil.pid_exists(pid)


class LockManager:
    def __init__(self, file_path):
        self.lock_file = file_path

    def acquire_control(self):
        """
        Acquires control by checking if a lock file exists. If the lock file does not exist, it creates one and writes the current process ID to it. If the lock file exists, it reads the process ID from it and compares it with the current process ID. If the process IDs match, it logs a message indicating that control is already acquired. If the process IDs do not match, it logs a message indicating that another instance of the program is already running with the process ID and exits.

        Parameters:
        - None

        Returns:
        - None
        """
        while os.path.exists(self.lock_file):
            with open(self.lock_file, "r", encoding="utf-8") as file:
                pid = file.read()
                if pid == str(os.getpid()):
                    logging.info("Control already acquired.")
                    return True
                elif check_pid_exists(int(pid)):
                    logging.info(
                        "Another instance of the program is already running with pid %s exiting...",
                        pid,
                    )
                    return False
                else:
                    # Remove stale lock
                    logging.info("removing stale lock")
                    self.release_control()

        with open(self.lock_file, "w", encoding="utf-8") as file:
            file.write(str(os.getpid()))
        logging.info("Control acquired.")
        return True

    def release_control(self):
        """
        Removes the lock file and prints a message indicating that control has been released.
        """
        if not os.path.exists(self.lock_file):
            logging.info("Lock does not exist.")
            raise LockError("Lock does not exist.")
        os.remove(self.lock_file)
        logging.info("Control released.")


if __name__ == "__main__":
    lock_manager = LockManager("/home/shazib/Desktop/Folder/python/wallpaper_updates/wallpaper_updator.lock")
    lock_manager.release_control()
    lock_manager.acquire_control()
