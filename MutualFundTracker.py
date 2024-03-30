import asyncio
import hashlib
import logging
import os
import pathlib
import re
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import Tuple
from util.lock_manager import LockManager
import aiohttp
import pytz
import ujson as json

from models.day_change import InvestmentData, NavData, getInvestmentData

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


@asynccontextmanager
async def gdrive_context(folder_name, logger):
    gdrive = GDrive(folder_name, logger)
    try:
        yield gdrive
    finally:
        # Add any cleanup code here if needed
        pass


download = False

INDIAN_TIMEZONE = pytz.timezone("Asia/Kolkata")
DATA_PATH = pathlib.Path(__file__).parent.resolve().joinpath("data")
lock_file = os.path.join(DATA_PATH, "lock_file.lock")

lock_manager = LockManager(lock_file)

FOLDER_NAME = "MutualFund"

LOGGER_PATH = pathlib.Path(DATA_PATH).resolve().joinpath("logger.log").as_posix()

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
    with open(file=filename, mode="w") as f:
        json.dump(data, f, indent=indent)
    async with gdrive_context(FOLDER_NAME, logging.getLogger()) as gdrive:
        await gdrive._upload_async(filename)


def writeRawDataToFile(file_name: str, data: str) -> None:
    logging.info(f"writing raw string data to {file_name}")
    with open(file_name, "w") as file:
        file.write(data)


def writeToFile(file_name: pathlib.Path | str, data) -> None:
    logging.info("writing to a file asynchronouslhy")
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)


def readJsonFile(filename: str | pathlib.Path):
    logging.info("reading fileName = %s ", filename)
    if not pathlib.Path(filename).exists() or download:
        GDrive(FOLDER_NAME, logging.getLogger()).download(filename)
    with open(filename, "r") as f:
        return json.load(f)


async def readJsonFileAsychronously(filename: str | pathlib.Path):
    logging.info("reading asynchronously fileName = %s", filename)
    if not pathlib.Path(filename).exists() or download:
        async with gdrive_context(FOLDER_NAME, logging.getLogger()) as gdrive:
            await gdrive._download_async(filename)

    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


class MutualFund:
    def __init__(self, is_downloadable: bool) -> None:
        if not lock_manager.acquire_control():
            sys.exit(0)
        self.is_downloadable = is_downloadable
        global download
        download = self.is_downloadable
        self.jsonData: InvestmentData = None  # type: ignore
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

    async def _intialiaze(self):
        logging.debug("----initializing----")
        units_tasks = asyncio.create_task(
            readJsonFileAsychronously(self.unitsFile), name="units"
        )
        order_tasks = asyncio.create_task(
            readJsonFileAsychronously(self.order_file), name="order"
        )
        daychange_tasks = asyncio.create_task(
            readJsonFileAsychronously(self.dayChangeJsonFileString), name="daychange"
        )

        results = await asyncio.gather(units_tasks, order_tasks, daychange_tasks)

        try:
            self.Units: dict = results[0]
        except JSONDecodeError:
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.Units = {}
            self.runOnceInitialization(self.unitsFile)
        try:
            self.Orders: dict = results[1]
        except JSONDecodeError:
            print("Something went wrong with the order file")
            self.Orders = {}
            self.runOnceInitialization(self.order_file)

        if not self.Units:
            print(
                f"No mutual Fund specified to track please Add something in {self.unitsFile} file to track"
            )
            exit(0)

        try:
            temp_data = results[2]
            self.jsonData: InvestmentData = getInvestmentData(temp_data)
        except (FileNotFoundError, JSONDecodeError):
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.runOnceInitialization(None)
        self.unitsKeyList = list(self.Units.keys())
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

    async def addToUnits(self, mfid, date) -> None:
        found = False
        if self.Orders.__contains__(mfid):
            if keys_list := list(self.Orders[mfid].keys()):
                for key in keys_list:
                    if self.check_past_dates(date, key):
                        order_data = self.Orders[mfid].pop(date)
                        data = self.Units[mfid]
                        data[0] += order_data[0]
                        data[1] += order_data[1]
                        found = True
        if found:
            self.tasks.extend(
                [
                    writeToFileAsync(self.unitsFile, self.Units),  # type: ignore
                    writeToFileAsync(self.order_file, self.Orders),  # type: ignore
                ]
            )

        else:
            logging.info(
                f"--No new Orders were found for {self.jsonData.funds[mfid].name}--"
            )
            logging.info(
                f"No new orders were found for {self.jsonData.funds[mfid].name}"
            )

    async def addToUnitsNotPreExisting(self) -> None:
        """
        Adds new mutual fund units to the unit file.
        """
        logging.info("--adding new MF units to Unit file")

        key_list = list(self.Orders.keys())
        found = False

        # Iterate over each key in the Orders dictionary
        for i in key_list:
            found = False
            if i not in self.Units:
                found = True
                self.Units[i] = [0, 0]

                date_list = list(self.Orders[i].keys())

                # Iterate over each date in the Orders dictionary for the current key
                for date in date_list:
                    date_data = self.Orders[i].pop(date)
                    self.Units[i][0] += date_data[0]
                    self.Units[i][1] += date_data[1]

                # Write the Units and Orders dictionaries to their respective files
                self.tasks.append(
                    [
                        writeToFileAsync(self.unitsFile, self.Units),  # type: ignore
                        writeToFileAsync(self.order_file, self.Orders),
                    ]
                )
        # If no new mutual fund was found in the Orders dictionary
        if not key_list or not found:
            logging.info("--No new Mutual fund was found in Order--")

    def addOrder(self, MFID: str, unit: float, amount: float, date: str) -> None:
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
            f"--Adding  Units={unit}, amount={amount}, date={date} to {self.jsonData.funds[MFID].name}--"
        )
        writeToFile(self.order_file, self.Orders)

    def runOnceInitialization(self, file) -> None:
        if not pathlib.Path.exists(DATA_PATH):
            pathlib.Path.mkdir(DATA_PATH)
        if file is not None:
            writeToFile(file, data=asdict(InvestmentData()))
        elif pathlib.Path.exists(self.dayChangeJsonFileStringBackupFile):
            backup_data = readJsonFile(self.dayChangeJsonFileStringBackupFile)
            writeToFile(self.dayChangeJsonFileString, backup_data)
            self.jsonData = getInvestmentData(backup_data)  # type: ignore
        else:
            writeToFile(
                self.dayChangeJsonFileStringBackupFile, asdict(InvestmentData())
            )
            self.jsonData = InvestmentData()

    def initializeTables(self) -> None:
        self.unitsKeyList = list(self.Units.keys())
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
            lastUpdated = self.jsonData.lastUpdated
            current = self.jsonData.sumTotal
            invested = self.jsonData.totalInvested
            totalProfitPercentage = self.jsonData.totalProfitPercentage
            totalProfit = self.jsonData.totalProfit
            totalDaychange = self.jsonData.totalDaychange
            totalDaychangePercentage = totalDaychange / invested * 100
        except KeyError:
            self.console.print(
                "Incomplete info in Json file try [b][yellow]-d y[/yellow][/b] option"
            )
            exit()

        investedString = f"Invested\n\n[bold]₹{invested}[/bold]"
        currentColor = (
            f"[green]₹{current}[/green]"
            if current >= invested
            else f"[red]₹{current}[/red]"
        )
        currentString = f"Current\n\n[bold]{currentColor}[/bold]"
        totalReturnString = "[yellow]•[/yellow]Total Returns\n\n[bold]" \
                            + f"{getfv(totalProfit)} {getfp(totalProfitPercentage)}[/bold]"
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
            preMF = self.jsonData.funds[id_]
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
        except Exception:
            self.console.print("Something went wrong")

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
        self.unitsKeyList = self.Units.keys()

    async def DayChangeTable(self):
        logging.info("--rendering day change table--")
        daily_table = Table(title="Day Change table", show_lines=True, expand=True)
        daily_table.add_column("SCHEME NAME", justify="center", no_wrap=True)
        daily_table.add_column("NAV", justify="center", no_wrap=True)
        daily_table.add_column("DayChange", justify="center", no_wrap=True)

        sumDayChange: dict = {}
        self.UpdateKeyList()
        for key in self.unitsKeyList:
            if not self.jsonData.funds.__contains__(key):
                await self.getCurrentValues()
            value = self.jsonData.funds[key].nav
            name: str = self.jsonData.funds[key].name
            units: float = self.Units[key][0]
            nav_col = ""
            daychange_col = ""
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
                nav_col += f"[yellow]{nav}[/yellow]\n"

                daychange_col += f"{getfv(daychangeData)}\n"
                prevDayChange = daychange

            daily_table.add_row(name, nav_col, daychange_col)

        if not self.console:
            self.console = Console()
        print("\n")
        self.console.print(daily_table)
        print("\n")
        self.dayChangeTableAll(sumDayChange)

    def drawTable(self):
        self.initializeTables()
        self.console = Console()
        self.summaryTableEdit()
        self.console.print(self.summaryTable)
        self.UpdateKeyList()
        for ids in self.unitsKeyList:
            self.MutualFundTableEdit(ids)
        self.console.print(self.TableMutualFund)

    def getGrepString(self) -> str:
        unitKeyList = list(self.Units.keys())

        return "".join(
            unitKeyList[i] if i == 0 else f"|{unitKeyList[i]}"
            for i in range(len(unitKeyList))
        )

    def drawGraph(self) -> None:
        for ids in self.unitsKeyList:
            value = self.jsonData.funds[ids]
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

    async def updateMyNaVFile(self):
        if self.nav_all_file is None and not self.downloadAllNavFile():
            return False

        pattern = self.getGrepString()
        result = "".join(
            i.strip() + "\n"
            for i in self.nav_all_file.splitlines()
            if re.search(pattern, i)
        )
        self.nav_my_file = result
        if self.jsonData.hash2 is not None:
            new_hash = hashlib.md5(self.nav_my_file.encode()).hexdigest()
            prev_hash = self.jsonData.hash2
            if prev_hash == new_hash:
                logging.info("--Nothing to update--")
                return False
            self.jsonData["hash2"] = new_hash
            lastUpdated = datetime.now(INDIAN_TIMEZONE).strftime(
                f"{self.formatString} %X"
            )
            self.jsonData["lastUpdated"] = lastUpdated
            self.tasks.append(
                writeToFileAsync(
                    self.dayChangeJsonFileStringBackupFile,
                    await readJsonFileAsychronously(self.dayChangeJsonFileString),
                )
            )

        return True

    async def write_backup(self):
        ...

    @retry(3)
    async def downloadAllNavFile(self) -> bool:
        logging.info("--downloading the NAV file from server--")
        start_time = time.time()

        async with aiohttp.client.ClientSession() as client:
            res = await client.get("https://www.amfiindia.com/spages/navopen.txt", timeout=5)
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
                if self.jsonData.hash:
                    prev_hash = self.jsonData.hash
                    if prev_hash == new_hash:
                        logging.info("--No changes found in the new NAV file--")
                        return False
                self.jsonData.hash = new_hash

                return True

    async def dayChangeMethod(
            self, ids: str, todayNav: float, latestNavDate: str, name: str
    ) -> float:
        self.isExistingId(ids, name, latestNavDate, todayNav)
        data = self.jsonData.funds[ids].nav
        latestDate = datetime.strptime(latestNavDate, self.formatString)

        prevDayNavDate: str = datetime.strftime(
            latestDate - timedelta(1), self.formatString
        )

        if prevDayNavDate not in data:
            key_list = list(data.keys())
            length = len(key_list)
            if length == 0:
                data[latestNavDate] = todayNav
                return -1
            elif length == 1 and key_list[-1] == latestNavDate:
                return -1
            elif key_list[-1] == latestNavDate:
                prevDayNavDate = key_list[-2]
            else:
                prevDayNavDate = key_list[-1]

        await self.addToUnits(ids, prevDayNavDate)
        units: float = self.Units[ids][0]

        prevDaySum: float = data[prevDayNavDate] * units
        dayChange: float = round(todayNav * units - prevDaySum, 3)
        self.jsonData.funds[ids]["dayChange"] = dayChange
        data[latestNavDate] = todayNav
        return dayChange

    def isExistingId(
            self, ids: str, name: str, latestNavDate: str, todayNav: float
    ) -> None:
        if not self.jsonData.funds.__contains__(ids):
            self.jsonData.funds[ids] = NavData()
            self.jsonData.funds[ids].name = name
            self.jsonData.funds[ids].nav = {latestNavDate: todayNav}
            self.jsonData.funds[ids].latestNavDate = latestNavDate

    async def cleanUp(self) -> None:
        keys: list[str] = list(self.jsonData.funds.keys())
        for key in keys:
            if key.isnumeric() and key not in self.Units:
                del self.jsonData.funds[key]

        self.tasks.append(
            writeToFileAsync(self.dayChangeJsonFileString, asdict(self.jsonData))
        )

    async def readMyNavFile(self) -> Tuple[float, float, float]:
        """
        returns subtotal, totalInvested , totaldaychange
        """

        sumTotal = 0
        totalInvested = 0
        totalDayChange = 0

        for line in self.nav_my_file.splitlines():
            temp = line.strip().split(";")
            _id, name, nav, date = (
                temp[0],
                temp[3].split("-")[0].strip(),
                float(temp[4]),
                temp[5],
            )

            # type: ignore
            dayChange: float = await self.dayChangeMethod(_id, nav, date, name)

            current = round(self.Units[_id][0] * nav, 3)
            invested = self.Units[_id][1]
            sumTotal += current
            totalInvested += invested
            if dayChange != -1:
                totalDayChange += dayChange

            cur_json_id = self.jsonData.funds[_id]
            cur_json_id["latestNavDate"] = date
            cur_json_id["current"] = current
            cur_json_id["invested"] = invested
            cur_json_id["dayChange"] = dayChange
        return sumTotal, totalInvested, totalDayChange

    async def getCurrentValues(self) -> None:

        logging.info("--Main calculation--")
        if self.is_downloadable:
            await self.addToUnitsNotPreExisting()
            if not await self.downloadAllNavFile():
                return

            if not await self.updateMyNaVFile():  # type: ignore
                return

        sumTotal, totalInvested, totalDaychange = await self.readMyNavFile()

        totalProfit = sumTotal - totalInvested
        totalProfitPercentage = totalProfit / totalInvested * 100

        totalProfitPercentage = round(totalProfitPercentage, 3)
        totalProfit = round(totalProfit, 3)
        totalDaychange = round(totalDaychange, 3)
        self.jsonData["totalProfit"] = totalProfit
        self.jsonData["sumTotal"] = round(sumTotal, 3)
        self.jsonData["totalInvested"] = totalInvested
        self.jsonData["totalProfitPercentage"] = totalProfitPercentage
        self.jsonData["totalDaychange"] = totalDaychange
        self.tasks.append(
            writeToFileAsync(self.dayChangeJsonFileString, data=asdict(self.jsonData))
        )

    async def del_cleanup(self):
        print("destructor called")
        await asyncio.gather(*self.tasks)

        self.tasks.clear()
        lock_manager.release_control()


@asynccontextmanager
async def mutualFundTracker(is_downloadable: bool = True) -> MutualFund:
    tracker = MutualFund(is_downloadable)
    await tracker._intialiaze()
    try:
        yield tracker
    finally:
        await tracker.del_cleanup()


async def main():
    async with mutualFundTracker(is_downloadable=True) as tracker:
        await tracker.getCurrentValues()
        tracker.drawTable()


if __name__ == "__main__":
    start = time.time()
    # asyncio.run(main())
    # print(time.time() - start)
    import cProfile

    cProfile.run(statement="asyncio.run(main())", sort="cumtime", filename="profile.out")
