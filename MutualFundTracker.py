import asyncio
import hashlib
import logging
import os
import pathlib
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import Tuple

import aiohttp
import logs.log_config as log_config  # type: ignore # noqa
import pytz
import ujson as json
from models.day_change import InvestmentData, NavData, getInvestmentData
from util.DesktopNotification import DesktopNotification

try:
    import plotext as plt
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print("Installing requirements for you")
    os.system("pip3 install -r requirements.txt")
    import plotext as plt
    from rich.console import Console
    from rich.table import Table

from util.retry import retry
from gdrive.GDrive import GDrive

download = False

INDIAN_TIMEZONE = pytz.timezone("Asia/Kolkata")
DATA_PATH = pathlib.Path(__file__).parent.resolve().joinpath("data")
lock_file = os.path.join(DATA_PATH, "lock_file.lock")

# lock_manager = LockManager(lock_file)

FOLDER_NAME = "MutualFund"


def roundUp3(number: float) -> float:
    return round(number, 3)


def getfv(number: float) -> str:
    return (
        f"[green]+₹{roundUp3(number)}[/green]"
        if number >= 0
        else f"[red]-₹{abs(roundUp3(number))}[/red]"
    )


def getfp(percentage: float) -> str:
    return (
        f"[green]({roundUp3(percentage)}%)[/green]"
        if percentage >= 0
        else f"[red]({roundUp3(percentage)})%[/red]"
    )


async def writeToFileAsync(filename: pathlib.Path, data: dict, indent=4) -> None:
    logging.info(f"writing asynchronously to {filename=}")
    with open(file=filename, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)
    # async with GDrive(FOLDER_NAME) as gdrive:  // no profit of using events because we are using context managers, and it will trigger __aexit__ method
    #     gdrive.upload_event(filename)
    await GDrive(FOLDER_NAME).upload_async(filename)


def writeRawDataToFile(file_name: str, data: str) -> None:
    logging.info(f"writing raw string data to {file_name}")
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(data)


def writeToFile(file_name: pathlib.Path | str, data) -> None:
    logging.info("writing to a file asynchronously")
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)


def readJsonFile(filename: str | pathlib.Path):
    logging.info("reading fileName = %s ", filename)
    if not pathlib.Path(filename).exists() or download:
        GDrive(FOLDER_NAME).download(filename)
    with open(filename, "r") as f:
        return json.load(f)


async def readJsonFileAsynchronously(filename: str | pathlib.Path):
    logging.info("reading asynchronously fileName = %s", filename)
    if not pathlib.Path(filename).exists() or download:
        async with GDrive(FOLDER_NAME) as gdrive:
            await gdrive.download_async(filename)

    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


class MutualFund:
    def __init__(self, is_downloadable: bool) -> None:

        self.Orders = None
        self.units = None
        self.Orders: dict[str:dict[str:list]]
        self.formatString = None
        self.units: dict
        self.is_downloadable = is_downloadable
        global download
        download = self.is_downloadable
        self.json_data: InvestmentData = None  # type: ignore
        self.console = Console()  # type: ignore
        self.unitsKeyList = []
        self.summaryTable = Table()
        self.TableMutualFund = Table()
        self.tasks: list = []
        self.nav_all_file = ""
        self.nav_my_file = ""
        logging.info("Initializing MutualFundTracker")
        logging.info("--Application has started---")
        logging.info("--Logged in as %s --", os.environ.get("USER"))

        self.logging = logging

        self.directoryString: str = pathlib.Path(__file__).parent.resolve().as_posix()
        self.sender_email: str = os.environ.get("shazmail")  # type: ignore
        self.password: str = os.environ.get("shazPassword")  # type: ignore

        self.order_file: pathlib.Path = DATA_PATH.joinpath("order.json")

        self.dayChangeJsonFileString: pathlib.Path = DATA_PATH.joinpath(
            "dayChange.json"
        )
        self.dayChangeJsonFileStringBackupFile: pathlib.Path = DATA_PATH.joinpath(
            "dayChange_bkc.json"
        )
        self.unitsFile: pathlib.Path = DATA_PATH.joinpath("units.json")

    async def initialize(self):
        logging.debug("----initializing----")
        units_tasks = asyncio.create_task(
            readJsonFileAsynchronously(self.unitsFile), name="units"
        )
        order_tasks = asyncio.create_task(
            readJsonFileAsynchronously(self.order_file), name="order"
        )
        daychange_tasks = asyncio.create_task(
            readJsonFileAsynchronously(self.dayChangeJsonFileString), name="daychange"
        )

        results = await asyncio.gather(units_tasks, order_tasks, daychange_tasks)

        try:
            self.units: dict = results[0]
        except JSONDecodeError:
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.units = {}
            self.run_once_initialization(self.unitsFile)
        try:
            self.Orders: dict[str:dict[str:list]] = results[1]
        except JSONDecodeError:
            print("Something went wrong with the order file")
            self.Orders = {}
            self.run_once_initialization(self.order_file)

        if not self.units:
            print(f"No mutual Fund specified to track please Add something in {self.unitsFile} file to track")
            sys.exit(0)

        try:
            temp_data = results[2]
            self.json_data: InvestmentData = getInvestmentData(temp_data)
        except (FileNotFoundError, JSONDecodeError):
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.run_once_initialization(None)
        self.unitsKeyList = list(self.units.keys())
        self.console: Console
        self.TableMutualFund = Table()
        self.summaryTable = Table()
        self.formatString = "%d-%b-%Y"
        plt.datetime.set_datetime_form(date_form=self.formatString)

    def check_past_dates(self, NavDate: str, orderDate) -> bool:
        """
        to check whether the order date is equal or smaller than the (nav date - 1)
        orders date = 13-may
        nav -1 date = 13-may
        in this case the orders should move to units

        scenario 2

        order date = 12-May
        nav - 1 date = 13-May
        in this case orders should move to units file
        """
        nav_date_format = datetime.strptime(NavDate, self.formatString)  # type: ignore
        orderDateFormat = datetime.strptime(orderDate, self.formatString)
        return orderDateFormat <= nav_date_format

    async def addToUnits(self, mutualfund_id, date, name: str) -> None:
        if self.Orders.__contains__(mutualfund_id):
            for key in self.Orders[mutualfund_id]:
                if self.check_past_dates(date, key):
                    order_data = self.Orders[mutualfund_id].pop(date)
                    data = self.units[mutualfund_id]
                    data[0] += order_data[0]
                    data[1] += order_data[1]
                    logging.info("adding units: %s and amount: %s to units for %s",
                                 order_data[0], order_data[1], name)

                    self.tasks.extend(
                        [
                            writeToFileAsync(self.unitsFile, self.units),  # type: ignore
                            writeToFileAsync(self.order_file, self.Orders),  # type: ignore
                        ]
                    )

    async def addToUnitsNotPreExisting(self) -> None:
        """
        Adds new mutual fund units to the unit file.
        """
        for order_key in self.Orders:

            if order_key not in self.units and self.Orders[order_key]:
                self.units[order_key] = [0, 0]
                for date in self.Orders[order_key]:
                    date_data = self.Orders[order_key].pop(date)
                    self.units[order_key][0] += date_data[0]
                    self.units[order_key][1] += date_data[1]
                    logging.info(
                        "Adding new mf  units: %s and amount: %s to units for %s",
                        date_data[0],
                        date_data[1],
                        order_key
                    )

                # Write the Units and Orders dictionaries to their respective files
                self.tasks.extend(
                    [
                        writeToFileAsync(self.unitsFile, self.units),  # type: ignore
                        writeToFileAsync(self.order_file, self.Orders),
                    ]
                )

    def add_order(self, MFID: str, unit: float, amount: float, date: str) -> None:
        """
        mfid , unit : float , amount :float , date : for ex 07-May-2022
        """
        logging.info("--adding order to Unit file--")
        if self.Orders.__contains__(MFID) and self.Orders[MFID].__contains__(date):
            data = self.Orders[MFID][date]
            data[0] += unit
            data[1] += amount
        elif self.Orders.__contains__(MFID):
            self.Orders[MFID][date] = [unit, amount]
        else:
            self.Orders[MFID] = {date: [unit, amount]}
        logging.info(
            f"--Adding  Units={unit}, amount={amount}, date={date} to {self.json_data.funds[MFID].name}--"
        )
        writeToFile(self.order_file, self.Orders)

    def run_once_initialization(self, file) -> None:
        if not pathlib.Path.exists(DATA_PATH):
            pathlib.Path.mkdir(DATA_PATH)
        if file is not None:
            writeToFile(file, data=asdict(InvestmentData()))
        elif pathlib.Path.exists(self.dayChangeJsonFileStringBackupFile):
            backup_data = readJsonFile(self.dayChangeJsonFileStringBackupFile)
            writeToFile(self.dayChangeJsonFileString, backup_data)
            self.json_data = getInvestmentData(backup_data)  # type: ignore
        else:
            writeToFile(
                self.dayChangeJsonFileStringBackupFile, asdict(InvestmentData())
            )
            self.json_data = InvestmentData()

    def initializeTables(self) -> None:
        self.unitsKeyList = list(self.units.keys())
        if not self.unitsKeyList:  # type: ignore
            print("no Mutual Fund found")
            exit()
        self.TableMutualFund = Table(
            expand=True,
            show_lines=True,  # type: ignore
        )
        self.summaryTable = Table.grid(expand=True, pad_edge=True, padding=2)

        self.summaryTable.add_column("invested", justify="center", no_wrap=True)
        self.summaryTable.add_column("current", justify="right", no_wrap=True)
        self.summaryTable.add_column("total returns", justify="right", no_wrap=True)
        self.summaryTable.add_column("lastUpdated", justify="right", no_wrap=True)

        self.TableMutualFund.add_column("SCHEME NAME", justify="center")
        self.TableMutualFund.add_column("DAY CHANGE", justify="center")
        self.TableMutualFund.add_column("RETURNS", justify="center")
        self.TableMutualFund.add_column("CURRENT", justify="center")
        self.TableMutualFund.add_column("NAV", justify="center")

    def summaryTableEdit(self) -> None:
        try:
            lastUpdated = self.json_data.lastUpdated
            current = self.json_data.sumTotal
            invested = self.json_data.totalInvested
            totalProfitPercentage = self.json_data.totalProfitPercentage
            totalProfit = self.json_data.totalProfit
            totalDaychange = self.json_data.totalDaychange
            totalDaychangePercentage = totalDaychange / invested * 100
        except KeyError:
            self.console.print(
                "Incomplete info in Json file try [b][yellow]-d y[/yellow][/b] option"
            )
            sys.exit()

        investedString = f"Invested\n\n[bold]₹{invested}[/bold]"
        currentColor = (
            f"[green]₹{current}[/green]"
            if current >= invested
            else f"[red]₹{current}[/red]"
        )
        currentString = f"Current\n\n[bold]{currentColor}[/bold]"
        totalReturnString = (
                "[yellow]•[/yellow]Total Returns\n\n[bold]"
                + f"{getfv(totalProfit)} {getfp(totalProfitPercentage)}[/bold]"
        )
        dailyReturnString = f"[yellow]•[/yellow][bold]{getfv(totalDaychange)} {getfp(totalDaychangePercentage)}[/bold]"
        lastUpdatedString = f"Last Updated\n\n[b][yellow]{lastUpdated}[/yellow][/b]"
        self.summaryTable.add_row(
            investedString,
            currentString,
            totalReturnString + "\n" + dailyReturnString,
            lastUpdatedString,
        )

    def MutualFundTableEdit(self, id_: str) -> None:
        try:
            preMF = self.json_data.funds[id_]
            SchemeName = preMF.name
            dayChange = preMF.dayChange
            current = preMF.current
            invested = preMF.invested
            date = preMF.latestNavDate
        except KeyError:
            self.console.print(
                # type: ignore
                "Incomplete info in Json file try[yellow][b]-d y[/yellow][/b] option"
            )
            exit(256)
        except Exception as error_occurred:
            self.console.print(error_occurred.__cause__)

            exit(256)
        if dayChange != -1:
            dayChangePercentage: float = roundUp3(dayChange / invested * 100)
            dayChangeString = f"{dayChangePercentage}%\n\n[b]{getfv(dayChange)}[/b]"
        else:
            dayChangeString = "N.A.\n\n[b]N.A.[/b]"

        returns = roundUp3(current - invested)

        returnsPercentage = returns / invested * 100

        returnString = f"₹{returns}\n\n[b]{getfp(returnsPercentage)}[/b]"
        currentString = f"₹{current}\n\n[b]₹{invested}[/b]"
        nav_date = f"[yellow]{date}[/yellow]\n\n[b]{preMF.nav[date]}[/b]"

        self.TableMutualFund.add_row(
            SchemeName, dayChangeString, returnString, currentString, nav_date
        )

    def dayChangeTableAll(self, dic: dict) -> None:
        all_daily_table = Table(title="Day Change Total", show_lines=True, expand=True)
        all_daily_table.add_column("NAV", justify="center", no_wrap=True)
        all_daily_table.add_column("DayChange", justify="center", no_wrap=True)
        sum_daychange_sorted_keys = sorted(
            dic.keys(), key=lambda x: datetime.strptime(x, "%d-%b-%Y")
        )
        dic = {k: dic[k] for k in sum_daychange_sorted_keys}

        nav_col = ""
        dayChange_col = ""

        for nav, dayChange in dic.items():
            nav_col += f"[yellow]{nav}[/yellow]\n"
            dayChange_col += f"{getfv(dayChange)}\n"
        all_daily_table.add_row(nav_col, dayChange_col)
        self.console.print(all_daily_table)

        print(end="\n\n")
        dates: list = sum_daychange_sorted_keys
        dayChangeList: list = list(dic.values())
        plt.clear_figure()
        plt.plot_size(100, 30)
        plt.title("Day Change")
        plt.xlabel("Date", xside="upper")
        plt.ylabel("profit", yside="left")

        plt.plot_date(dates, dayChangeList, color="green", label="DayChange Plot")
        plt.clear_color()
        plt.show()

    def UpdateKeyList(self):
        self.unitsKeyList = self.units.keys()

    async def day_change_table(self):
        logging.info("--rendering day change table--")
        daily_table = Table(title="Day Change table", show_lines=True, expand=True)
        daily_table.add_column("SCHEME NAME", justify="center", no_wrap=True)
        daily_table.add_column("NAV", justify="center", no_wrap=True)
        daily_table.add_column("DayChange", justify="center", no_wrap=True)

        sum_day_change: dict = {}
        self.UpdateKeyList()
        for key in self.unitsKeyList:
            if not self.json_data.funds.__contains__(key):
                await self.get_current_values()
            value = self.json_data.funds[key].nav
            name: str = self.json_data.funds[key].name
            units: float = self.units[key][0]
            nav_col = ""
            daychange_col = ""
            i = True
            prev_day_change = 0.0

            for nav, daychange in value.items():
                if i:
                    prev_day_change = units * daychange
                    i = False
                    continue
                daychange *= units
                daychange_data: float = round(daychange - prev_day_change, 3)

                if nav in sum_day_change:
                    sum_day_change[nav] += daychange_data
                else:
                    sum_day_change[nav] = daychange_data
                nav_col += f"[yellow]{nav}[/yellow]\n"

                daychange_col += f"{getfv(daychange_data)}\n"
                prev_day_change = daychange

            daily_table.add_row(name, nav_col, daychange_col)

        if not self.console:
            self.console = Console()
        print("\n")
        self.console.print(daily_table)
        print("\n")
        self.dayChangeTableAll(sum_day_change)

    def draw_table(self):
        self.initializeTables()
        self.console = Console()
        self.summaryTableEdit()
        self.console.print(self.summaryTable)
        self.UpdateKeyList()
        for ids in self.unitsKeyList:
            self.MutualFundTableEdit(ids)
        self.console.print(self.TableMutualFund)

    def get_grep_string(self) -> str:
        unitKeyList = list(self.units.keys())

        return "".join(
            unitKeyList[i] if i == 0 else f"|{unitKeyList[i]}"
            for i in range(len(unitKeyList))
        )

    def draw_graph(self) -> None:
        for ids in self.unitsKeyList:
            value = self.json_data.funds[ids]
            print()
            x = value.nav.keys()
            y = value.nav.values()
            plt.plot_size(100, 30)
            plt.title(value["name"])
            plt.xlabel("Date", xside="upper")
            plt.ylabel("profit", yside="left")

            plt.plot_date(x, y, color="green", label="Nav Plot")
            plt.clear_color()

            plt.show()
            plt.clear_figure()
        print()

    async def update_my_nav_file(self):
        if self.nav_all_file is None and not self.download_all_nav_file():
            return False

        pattern = self.get_grep_string()
        result = "".join(
            i.strip() + "\n"
            for i in self.nav_all_file.splitlines()
            if re.search(pattern, i)
        )
        self.nav_my_file = result
        if self.json_data.hash2 is not None:
            new_hash = hashlib.md5(self.nav_my_file.encode()).hexdigest()
            prev_hash = self.json_data.hash2
            if prev_hash == new_hash:
                logging.info("--Nothing to update--")
                return False
            self.json_data.hash2 = new_hash
            lastUpdated = datetime.now(INDIAN_TIMEZONE).strftime(
                f"{self.formatString} %X"
            )
            self.json_data.lastUpdated = lastUpdated
            self.tasks.append(
                writeToFileAsync(
                    self.dayChangeJsonFileStringBackupFile,
                    await readJsonFileAsynchronously(self.dayChangeJsonFileString),
                )
            )
            DesktopNotification("Mutual Fund Tracker", f"Updated at {lastUpdated}")

        return True

    @retry(retries=3, delay=1, fail_after_retry_exhausted=False)
    async def download_all_nav_file(self) -> bool:
        logging.info("--downloading the NAV file from server--")

        async with aiohttp.client.ClientSession() as client:
            start_time = time.time()
            res = await client.get(
                "https://www.amfiindia.com/spages/navopen.txt", timeout=20
            )
            status = res.status
            text = await res.text()

            if status != 200:
                logging.error(f"HTTP status: {status}")
                raise ValueError(f"HTTP status: {status}")

            else:
                self.nav_all_file = text
                logging.info(
                    f"--took {(time.time() - start_time):.2f} Secs to download the file"
                )
                new_hash = hashlib.md5(self.nav_all_file.encode()).hexdigest()
                if self.json_data.hash:
                    prev_hash = self.json_data.hash
                    if prev_hash == new_hash:
                        logging.info("--No changes found in the new NAV file--")
                        return False
                self.json_data.hash = new_hash

                return True

    async def day_change_method(
            self, ids: str, today_nav: float, latest_nav_date: str, name: str
    ) -> float:
        self.is_existing_id(ids, name, latest_nav_date, today_nav)
        data = self.json_data.funds[ids].nav
        latestDate = datetime.strptime(latest_nav_date, self.formatString)

        prev_day_nav_date: str = datetime.strftime(
            latestDate - timedelta(1), self.formatString
        )

        if prev_day_nav_date not in data:
            key_list = list(data.keys())
            length = len(key_list)
            if length == 0:
                data[latest_nav_date] = today_nav
                return -1
            elif length == 1 and key_list[-1] == latest_nav_date:
                return -1
            elif key_list[-1] == latest_nav_date:
                prev_day_nav_date = key_list[-2]
            else:
                prev_day_nav_date = key_list[-1]

        await self.addToUnits(ids, prev_day_nav_date, name)
        units: float = self.units[ids][0]

        prevDaySum: float = data[prev_day_nav_date] * units
        dayChange: float = round(today_nav * units - prevDaySum, 3)
        self.json_data.funds[ids].dayChange = dayChange
        data[latest_nav_date] = today_nav
        return dayChange

    def is_existing_id(
            self, ids: str, name: str, latest_nav_date: str, today_nav: float
    ) -> None:
        if not self.json_data.funds.__contains__(ids):
            self.json_data.funds[ids] = NavData()
            self.json_data.funds[ids].name = name
            self.json_data.funds[ids].nav = {latest_nav_date: today_nav}
            self.json_data.funds[ids].latestNavDate = latest_nav_date

    async def clean_up(self) -> None:
        keys: list[str] = list(self.json_data.funds.keys())
        for key in keys:
            if key.isnumeric() and key not in self.units:
                del self.json_data.funds[key]

        self.tasks.append(
            writeToFileAsync(self.dayChangeJsonFileString, asdict(self.json_data))
        )

    async def read_my_nav_file(self) -> Tuple[float, float, float]:
        """
        returns subtotal, total_invested , totaldaychange
        """

        sum_total = 0
        total_invested = 0
        total_day_change = 0

        for line in self.nav_my_file.splitlines():
            temp = line.strip().split(";")
            _id, name, nav, date = (
                temp[0],
                temp[3].split("-")[0].strip(),
                float(temp[4]),
                temp[5],
            )

            # type: ignore
            dayChange: float = await self.day_change_method(_id, nav, date, name)

            current = round(self.units[_id][0] * nav, 3)
            invested = self.units[_id][1]
            sum_total += current
            total_invested += invested
            if dayChange != -1:
                total_day_change += dayChange

            cur_json_id = self.json_data.funds[_id]
            cur_json_id.latestNavDate = date
            cur_json_id.current = current
            cur_json_id.invested = invested
            cur_json_id.dayChange = dayChange
        return sum_total, total_invested, total_day_change

    async def get_current_values(self) -> None:

        logging.info("--Main calculation--")
        if self.is_downloadable:
            await self.addToUnitsNotPreExisting()
            if not await self.download_all_nav_file():
                return

            if not await self.update_my_nav_file():  # type: ignore
                return

        sum_total, total_invested, total_daychange = await self.read_my_nav_file()

        total_profit = sum_total - total_invested
        total_profit_percentage = total_profit / total_invested * 100

        total_profit_percentage = round(total_profit_percentage, 3)
        total_profit = round(total_profit, 3)
        total_daychange = round(total_daychange, 3)

        self.json_data.totalProfit = total_profit
        self.json_data.sumTotal = round(sum_total, 3)
        self.json_data.totalInvested = total_invested
        self.json_data.totalProfitPercentage = total_profit_percentage

        self.json_data.totalDaychange = total_daychange
        self.tasks.append(
            writeToFileAsync(self.dayChangeJsonFileString, data=asdict(self.json_data))
        )

    async def del_cleanup(self):
        """

        :return:
        """
        if self.tasks:
            start_time = time.time()

            await asyncio.gather(*self.tasks)

            logging.debug(f"---Took {(time.time() - start_time):.2f} Secs to complete the tasks---")
        else:
            logging.debug("No tasks to run")

        self.tasks.clear()
        # lock_manager.release_control()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.del_cleanup()
        return False


async def main2():
    async with MutualFund(is_downloadable=True) as tracker:
        await tracker.get_current_values()
        tracker.draw_table()


if __name__ == "__main__":
    start = time.time()
    import cProfile

    cProfile.run(
        statement="asyncio.run(main2())", sort="cumtime", filename="profile.out"
    )
