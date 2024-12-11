import socket
from functools import lru_cache


@lru_cache(maxsize=1)
def check_internet_connection():
    """
    Checks if there is an active internet connection.

    This function is lru cached with a max size of 1, meaning it will only be called once per session.
    It will attempt to connect to www.google.com and return True if the connection is successful.
    If the connection fails, it will print a message and return False.

    :return: True if there is an active internet connection, False otherwise
    :rtype: bool
    """
    try:
        # Connect to a well-known website
        print("checking for internet connection")
        socket.create_connection(("www.google.com", 80))
        print("internet connection is available")
        return True
    except OSError:
        print("no interest connection is found")
        return False


if __name__ == "__main__":
    for i in range(100):
        check_internet_connection()
