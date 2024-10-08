import asyncio
import logging
import pathlib
import sys
from datetime import datetime

import nsepy
import requests
import ujson as json
from pandas import DataFrame

sys.path.append(pathlib.Path(__file__).parent.parent.parent.absolute().as_posix())

from gdrive.GDrive import (
    GDrive,
)
from models.day_change import (
    InvestmentData,
    get_investment_data
)

data_path = (
    pathlib.Path(__file__).parent.parent.parent.joinpath("data").resolve().as_posix()
)
LOGGER_PATH = pathlib.Path(data_path).parent.joinpath("logs").resolve().joinpath("logger.log").as_posix()

formatter = logging.Formatter(
    "%(levelname)s - (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])"
)
formatter.datefmt = "%m/%d/%Y %I:%M:%S %p"

logging.basicConfig(
    filename=LOGGER_PATH,
    filemode="a",
    level=logging.INFO,
    format="%(levelname)s - (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logging.getLogger().addHandler(stream_handler)


def log_uncaught_exceptions(exctype, value, traceback):
    logging.exception("Uncaught exception", exc_info=(exctype, value, traceback))


sys.excepthook = log_uncaught_exceptions

# gdrive: GDrive = GDrive("MutualFund")


FOLDER_NAME: str = "MutualFund"  # type: ignore


def roundup3(value: float) -> float:
    return round(value, 3)


async def readJsonFileAsynchronously(filename: str | pathlib.Path):
    logging.info(f"reading asynchronously {filename=}")
    async with GDrive(FOLDER_NAME) as gdrive:
        await gdrive.download_async(filename)
    with open(filename, "r") as f:
        return json.load(f)


def readJsonFromDataFolder(filename):
    file_path = pathlib.Path(data_path).joinpath(filename).resolve()
    GDrive(FOLDER_NAME).download(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def readJsonFromDataFolderAsychronously(filename):
    file_path = pathlib.Path(data_path).joinpath(filename).resolve()
    await GDrive(FOLDER_NAME).download_async(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def readJsonFile(filename: str | pathlib.Path):
    logging.info(f"reading {filename=}")

    GDrive(FOLDER_NAME).download(filename)
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def writeRawDataToFile(file_name: str, data: str) -> None:
    logging.info(f"writing raw string data to {file_name}")
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(data)


async def write_to_file_async(
        filename: pathlib.Path, data: dict, indent=4
) -> None:
    logging.info(f"writing asynchronously to {filename=}")
    with open(filename, mode="w") as f:
        # f.write(json.dumps(obj=data, indent=indent))
        # noinspection PyTypeChecker
        json.dump(data, f, indent=indent)
    async with GDrive(FOLDER_NAME) as gdrive:
        await gdrive.upload_async(filename)


def writeToFile(filename: pathlib.Path, data: object, indent=4) -> None:
    logging.info(f"writing to {filename=}")
    with open(filename, "w") as f:
        # noinspection PyTypeChecker
        json.dump(data, f, indent=indent)
    GDrive(FOLDER_NAME).upload(filename)


def get_history(symbol: str, start: str, end: str) -> DataFrame:
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    return nsepy.get_history(symbol, start=start_date, end=end_date)


class helper_functions:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initiated = False
        else:
            cls._initiated = True
        return cls._instance

    def __init__(self):
        if self._initiated:
            print("Already initialized")
            return
        self.json_data = None
        self.mutual_funds_dic = None
        self.stock_data = None
        self.stock_order = None
        self.daychange_json:InvestmentData = None
        self.unit_json = None
        self.mutual_funds = None
        self.order = None
        self.tasks = None
        self.unit_file_path = pathlib.Path(data_path).joinpath("units.json").resolve()
        self.daychange_file_path = (
            pathlib.Path(data_path).joinpath("dayChange.json").resolve()
        )
        self.order_file_path = pathlib.Path(data_path).joinpath("order.json").resolve()
        self.json_data_file_path = (
            pathlib.Path(data_path).joinpath("NAVAll.json").resolve()
        )
        self.stock_data_file_path = (
            pathlib.Path(data_path).joinpath("stocks_data.json").resolve()
        )
        self.stock_order_file_path = (
            pathlib.Path(data_path).joinpath("stock_order.json").resolve()
        )
        self.stock_order: dict
        self.stock_data: dict

        self.unit_json: dict
        self.daychange_json: InvestmentData
        self.order: dict
        self.tasks: list[asyncio.tasks.Task]

        asyncio.run(self.load_on())

    async def load_on(self):
        file_list = [
            self.daychange_file_path,
            self.unit_file_path,
            self.order_file_path,
            self.stock_order_file_path,
            self.stock_data_file_path,
        ]
        self.tasks = [
            asyncio.create_task(
                readJsonFileAsynchronously(file), name=file.as_posix()
            )
            for file in file_list
        ]
        self.tasks.append(
            asyncio.create_task(
                asyncio.to_thread(self.create_index_all_mutual_fund),
                name="create_index_all_mutual_fund",
            )
        )

        results, _ = await asyncio.wait(self.tasks)

        for result in results:
            print(result.get_name())
            if result.get_name() == "create_index_all_mutual_fund":
                continue
            elif result.get_name() == self.daychange_file_path.as_posix():
                self.daychange_json = get_investment_data(result.result())
            elif result.get_name() == self.unit_file_path.as_posix():
                self.unit_json = result.result()

            elif result.get_name() == self.order_file_path.as_posix():
                self.order = result.result()
            elif result.get_name() == self.stock_order_file_path.as_posix():
                self.stock_order = result.result()
            elif result.get_name() == self.stock_data_file_path.as_posix():
                self.stock_data = result.result()

        self.tasks.clear()
        self.mutual_funds_dic = {
            self.daychange_json.funds[unit].name: unit for unit in self.unit_json
        }
        self.mutual_funds = list(self.mutual_funds_dic.keys())

    def add_order_stock(self, stock, units, amount):
        stock_order = self.stock_order
        stock_data = self.stock_data
        if not stock_data.__contains__(stock):
            return False
        if stock_order.__contains__(stock):
            stock_order[stock][0] += units
            stock_order[stock][1] += amount * units
        else:
            stock_order[stock] = [units, amount * units]
        # self.tasks_another.append(
        #     self.loop_another.create_task(
        #     self.writeToFileAsync(self.stock_order_file_path, stock_order)
        #     )
        #     )
        writeToFile(self.stock_order_file_path, stock_order)
        return True

    def add_order(self, MFID, unit, amount, date) -> str:
        """
        mfid , unit : float , amount :float , date : for ex 07-May-2022
        """
        value = "old"
        if self.order.__contains__(MFID) and self.order[MFID].__contains__(date):
            data = self.order[MFID][date]
            data[0] += unit
            data[1] += amount
        elif self.order.__contains__(MFID):
            self.order[MFID][date] = [unit, amount]
        else:
            self.order[MFID] = {date: [unit, amount]}
            value = "new"

        writeToFile(self.order_file_path, self.order)
        return value

    def getDailyChange(self):
        sumDayChange: dict = {}
        units_json = self.unit_json
        daychange_json = self.daychange_json

        for val in units_json.keys():
            value: dict[str, float] = daychange_json.funds[val].nav
            units: float = units_json[val][0]
            i = True
            prevDayChange = 0.0
            for nav, daychange in value.items():
                if i:
                    prevDayChange = units * daychange
                    i = False
                    continue
                daychange *= units
                daychangeData: float = round(daychange - prevDayChange, 3)

                if nav in sumDayChange:
                    sumDayChange[nav] += daychangeData
                else:
                    sumDayChange[nav] = daychangeData
                prevDayChange = daychange
        sum_daychange_sorted_keys = sorted(
            sumDayChange.keys(), key=lambda x: datetime.strptime(x, "%d-%b-%Y")
        )
        # sorted by key, return a dict
        sumDayChange = {k: sumDayChange[k] for k in sum_daychange_sorted_keys}
        return [
            {
                "x": list(sumDayChange.keys()),
                "y": list(sumDayChange.values()),
                "type": "line",
                "name": "Daily Change",
            }
        ]

    def dailyChangePerMutualFund(self, id_):

        sumDayChange: dict = {}
        units_json = self.unit_json
        daychange_json = self.daychange_json

        units: float = units_json[id_][0]
        value = daychange_json.funds[id_]["nav"]
        i = True
        prevDayChange = 0.0
        for nav, daychange in value.items():
            if i:
                prevDayChange = units * daychange
                i = False
                continue
            daychange *= units
            daychangeData: float = round(daychange - prevDayChange, 3)

            if nav in sumDayChange:
                sumDayChange[nav] += daychangeData
            else:
                sumDayChange[nav] = daychangeData
            prevDayChange = daychange
        return [
            {
                "x": list(sumDayChange.keys()),
                "y": list(sumDayChange.values()),
                "type": "line",
                "name": daychange_json.funds[id_]["name"] + " Daily Change",
            }
        ], daychange_json.funds[id_]["name"]

    def return_data(self, value):
        daychange_json = self.daychange_json

        data = daychange_json.funds[value]["nav"]
        x = list(data.keys())
        y = list(data.values())
        return_list = [
            {
                "x": x,
                "y": y,
                "type": "line",
                "name": daychange_json.funds[value].name,
            }
        ]
        return return_list, daychange_json.funds[value]["name"]

    def get_options(self):
        print(self.mutual_funds_dic, self.mutual_funds)
        mutual_funds_dic = self.mutual_funds_dic
        mutual_funds = list(self.mutual_funds_dic.keys())
        return [{"label": x, "value": mutual_funds_dic[x]} for x in mutual_funds]

    def getInvestmentDistribution(self):
        data_at_time_of_investment = {}
        data_current = {}
        units_json = self.unit_json
        daychange_json = self.daychange_json

        for val in units_json.keys():
            mutual_fund = daychange_json.funds[val]
            data_current[mutual_fund.name] = mutual_fund.current
            data_at_time_of_investment[mutual_fund.name] = mutual_fund.invested
        return data_at_time_of_investment, data_current

    def getMainTableData(self):
        units_json = self.unit_json
        daychange_json = self.daychange_json

        lastUpdated = daychange_json["lastUpdated"]
        current = daychange_json["sumTotal"]
        invested = daychange_json["totalInvested"]
        totalProfitPercentage = daychange_json["totalProfitPercentage"]
        totalProfit = daychange_json["totalProfit"]
        summaryTable = [
            ["Invested", "Current", "•Total Returns", "Last UpDated"],
            [
                invested,
                current,
                f"{str(totalProfit)} {str(totalProfitPercentage)}",
                lastUpdated,
            ],
        ]
        mutual_fund_table: list[list] = [
            "SCHEME NAME,DAY CHANGE,RETURNS,CURRENT,NAV".split(",")
        ]

        for val in units_json.keys():
            preMF = daychange_json.funds[val]
            SchemeName = preMF["name"]
            dayChange = preMF["dayChange"]
            current = preMF["current"]
            invested = preMF["invested"]
            date = preMF["latestNavDate"]
            if dayChange != "N.A.":
                # print(dayChange)
                dayChangePercentage = roundup3(dayChange / invested * 100)
                daychange_string = f"{dayChangePercentage}% {dayChange}"
            else:
                daychange_string = "N.A. N.A."
            returns = roundup3(current - invested)
            returnsPercentage = roundup3(returns / invested * 100)
            returnsString = f"{returns} {returnsPercentage}%"
            currentString = f"{current} {invested}"
            nav_date = f'{date} {preMF["nav"][date]}'
            mutual_fund_table.append(
                [SchemeName, daychange_string, returnsString, currentString, nav_date]
            )

        return summaryTable, mutual_fund_table

    def create_index_all_mutual_fund(self):
        index_all_mutual_fund = {}
        with requests.get("https://www.amfiindia.com/spages/NAVopen.txt") as response:
            for line in response.text.splitlines():
                if line == "":
                    continue
                if line[0].isdigit():
                    data = line.split(";")
                    try:
                        index_all_mutual_fund[data[3]] = data[0]
                    except IndexError:
                        continue
        self.json_data: dict = index_all_mutual_fund
        # writeToFile(self.json_data_file_path, index_all_mutual_fund) # no point of writing it to the gdrive
        # self.tasks_no_want_to_wait_till_finish.append(self.loop.create_task(self.writeToFileAsync(
        #     self.json_data_file_path , index_all_mutual_fund
        #         )))
        return self.json_data

    def get_index_all_mutual_fund(self):
        return [{"label": x, "value": y} for x, y in self.json_data.items()]

    def get_id_name_dic(self, value):
        json_data = self.json_data
        value = str(value)
        key = [k for k, v in json_data.items() if value == v]
        return key[0]

    def get_all_stocks_list(self):
        stock_data = self.stock_data
        return [{"label": stock_data[x], "value": x} for x in stock_data]

    def get_all_stock_dic(self):
        return self.stock_data


if __name__ == "__main__":
    # create_index_all_mutual_fund()
    obj = helper_functions()
