import datetime
import json
import os
from pathlib import Path

directory_path = Path(__file__).parent.parent

data_directory = os.path.join(directory_path, "data")

unit_file = os.path.join(data_directory, "units.json")


def read_json(fileName: str) -> dict:
    """
    Reads the given json file and returns its content as a dictionary.

    Args:
        fileName (str): The name of the file to be read.

    Returns:
        dict: The content of the file as a dictionary.
    """
    with open(fileName, "r") as file:
        data = json.load(file)
    return data


def writeJson(fileName: str, data: dict) -> None:
    """
    Writes the given data to the given file.

    Args:
        fileName (str): The name of the file to be written.
        data (dict): The data to be written to the file.
    """
    with open(fileName, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def sort_nav_data_based_on_nav_date(fileName: str) -> None:
    """
    Sorts the nav data based on the nav date.

    Sorts the nav data of all the mutual funds in the given file based on the nav date.

    Args:
        fileName (str): The name of the file containing the nav data.

    Returns:
        None
    """
    data = read_json(fileName)
    for key in read_json(unit_file).keys():
        sorted_dates = sorted(
            data["funds"][key]["nav"].keys(),
            key=lambda x: datetime.datetime.strptime(x, "%d-%b-%Y"),
        )
        sorted_dict = {date: data["funds"][key]["nav"][date] for date in sorted_dates}
        data["funds"][key]["nav"] = sorted_dict

    writeJson(fileName, data)


if __name__ == "__main__":
    sort_nav_data_based_on_nav_date(os.path.join(data_directory, "dayChange.json"))
else:
    raise ImportError("This file is not meant to be imported")
