import logging
import os
import pathlib
import sys
from datetime import datetime

sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
import pytz

from EmailService.send_mail import EmailService  # autopep8: off

try:
    from pydrive.auth import GoogleAuth, RefreshError
    from pydrive.drive import GoogleDrive
except ImportError:
    if os.name == "nt":
        os.system("pip install pydrive")
    else:
        os.system("pip3 install  pydrive")
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive

CRED_FILE = pathlib.Path(__file__).parent.joinpath(
    "credentials.json").resolve()

FILE_PATH = pathlib.Path(__file__).parent.parent.joinpath(
    "data", "dayChange.json").resolve()

CLIENT_SECRET = pathlib.Path(__file__).parent.joinpath(
    "client_secrets.json").resolve()

if not os.path.exists(CLIENT_SECRET):
    raise FileNotFoundError(
        f"Client secret file not found at {CLIENT_SECRET}")

LOCAL_DATE_TIMEZONE = pytz.timezone("Asia/Kolkata")


logger_path = pathlib.Path(__file__).parent.parent.joinpath(
    "data", "logger.log").resolve()

if not os.path.exists(logger_path):
    open(logger_path, "w").close()

logging.basicConfig(
    filename=logger_path,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)


class GDrive:
    def __init__(self, folder_name="MutualFund"):
        self.gauth = GoogleAuth()
        self.gauth.settings['client_config_file'] = CLIENT_SECRET
        if os.path.exists(CRED_FILE):
            self.gauth.LoadCredentialsFile(CRED_FILE)
        else:
            self.gauth.LocalWebserverAuth()
            self.gauth.SaveCredentialsFile(CRED_FILE)
        if self.gauth.credentials is None:
            self.gauth.LocalWebserverAuth()
            self.gauth.SaveCredentialsFile(CRED_FILE)
        if self.gauth.access_token_expired:
            try:
                self.gauth.Refresh()
            except RefreshError as e:
                logging.error("Error while refreshing token.")
                EmailService().send_mail(
                    subject="Error while refreshing token.", body=str(e))
                exit(1)
            self.gauth.SaveCredentialsFile(CRED_FILE)

        self.drive = GoogleDrive(self.gauth)
        self.folder = self.create_or_get_folder(folder_name)

    def create_or_get_folder(self, folder_name):
        folder_list = self.drive.ListFile(
            {'q': f"title='{folder_name}' and trashed=false and mimeType='application/vnd.google-apps.folder'"}).GetList()
        if len(folder_list) == 0:
            folder = self.drive.CreateFile(
                {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'})
            folder.Upload()
            logging.info(
                f"Folder '{folder_name}' with Folder_id {folder['id']} created on Google Drive.")
        else:
            folder = folder_list[0]
            logging.info(
                f"Folder '{folder_name}' with Folder_id {folder['id']} found on Google Drive.")
        return folder

    def upload(self, file_path=FILE_PATH):
        self.file_title = os.path.basename(file_path)

        try:
            self.file_list = self.drive.ListFile(
                {'q': f"title='{self.file_title}' and trashed=false and '{self.folder['id']}' in parents"}).GetList()
        except Exception as e:
            logging.error("Error while getting file list from Google Drive.")
            return
        if len(self.file_list) == 0:
            self.file = self.drive.CreateFile(
                {'title': self.file_title, 'parents': [{'id': self.folder['id']}]})
        else:
            self.file = self.file_list[0]
        if os.path.exists(file_path):
            local_file_modified_time = os.path.getmtime(file_path) + 10
        else:
            local_file_modified_time = 0

        if len(self.file_list) > 0:
            # +10 microsecond to avoid the time difference between local and remote because of the upload time

            if local_file_modified_time <= self.get_remote_modified_timestamp():
                logging.info(
                    f"File '{self.file_title}' is up to date on Google Drive. skipping upload.")
                return

        self.file_title = os.path.basename(file_path)
        try:
            self.file.SetContentFile(file_path)
            self.file.Upload()
        except Exception as e:
            logging.error(
                f"Error while uploading file '{self.file_title}' with error {e}")

        logging.info(
            f"File '{self.file_title} and {file_path}' uploaded to Google Drive.")

    def get_remote_modified_timestamp(self):
        remote_file_modified_time = datetime.strptime(
            self.file['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        remote_file_modified_time = remote_file_modified_time.replace(
            tzinfo=pytz.utc)
        remote_file_modified_time = remote_file_modified_time.astimezone(
            LOCAL_DATE_TIMEZONE)
        return remote_file_modified_time.timestamp()

    def download(self, file_path=FILE_PATH):
        self.file_title = os.path.basename(file_path)
        try:
            self.file_list = self.drive.ListFile(
                {'q': f"title='{self.file_title}' and trashed=false"}).GetList()
        except Exception as e:
            logging.error("Error while getting file list from Google Drive.")
            return False
        if len(self.file_list) == 0:
            self.file = self.drive.CreateFile(
                {'title': self.file_title})
        else:
            self.file = self.file_list[0]

        if os.path.exists(file_path):
            local_file_modified_time = os.path.getmtime(file_path) + 10
        else:
            local_file_modified_time = 0

        try:
            if local_file_modified_time >= self.get_remote_modified_timestamp():
                logging.info(
                    f"File '{self.file_title}' is up to date on local. skipping download.")
                return False
        except Exception as e:
            logging.info(f"File '{self.file_title}' is not present on remote.")
            print(e)

            return False
        try:
            self.file.GetContentFile(file_path)
        except Exception as e:
            logging.error(
                f"Error while downloading file '{self.file_title}' with error {e}")
            return False

        logging.info(
            f"File '{self.file_title}' downloaded to {file_path} from Google Drive.")
        return True


if __name__ == "__main__":
    gdrive = GDrive()
    print(f"{logger_path=} {CRED_FILE=} {FILE_PATH=} {CLIENT_SECRET=}")
