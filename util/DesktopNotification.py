import subprocess
import os
import pathlib

# Set correct DISPLAY and DBUS_SESSION_BUS_ADDRESS
os.environ["DISPLAY"] = ":1"
os.environ["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1000/bus"

pwd = pathlib.Path(__file__).parent.parent.resolve()
icon_image = pathlib.Path(pwd, "data", "icon.jpg").as_posix()

class DesktopNotification:
    def __init__(self, title: str, message: str):
        """
        Initializes a desktop notification with the given title and message.

        Parameters:
            title (str): The title of the notification.
            message (str): The message body of the notification.
        """
        try:
            subprocess.run(["notify-send", title, message, "-i", icon_image, "-t", "10000"])
        except Exception as e:
            print(f"Error sending notification: {e}")

if __name__ == "__main__":
    DesktopNotification("Test Notification", "This should stay visible for 10 seconds")
    print("done")
