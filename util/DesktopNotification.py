import logging
import os
import pathlib

import plyer

os.environ["DISPLAY"] = ":0"
os.environ["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1000/bus"

pwd = pathlib.Path(__file__).parent.parent.resolve()
icon_image = pathlib.Path(pwd, "data", "icon.jpg").as_posix()

# print(icon_image)


class DesktopNotification:

    def __init__(self, title: str, message: str):
        """
        Initializes a Birthday notification with the given title and message.

        Parameters:
            title (str): The title of the notification.
            message (str): The message body of the notification.

        Returns:
            None
        """
        try:
            plyer.notification.notify(
                title=title,
                message=message,
                app_name="MutualFundTracker",
                timeout=10,
                ticker="MutualFundTracker",
                toast=True,
                app_icon=icon_image,
            )
        except Exception as e:
            logging.error(e)
        # Not working cause of X11 and cron job issue have to add cron username to group of either video or x11 don't
        # know much about .


if __name__ == "__main__":
    DesktopNotification("test", "test")
    print("done")
