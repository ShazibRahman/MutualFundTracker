import socket


def check_internet_connection():
    try:
        # Connect to a well-known website
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False
