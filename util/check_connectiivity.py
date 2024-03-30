import socket
from functools import lru_cache


@lru_cache(maxsize=2)
def check_internet_connection():
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
