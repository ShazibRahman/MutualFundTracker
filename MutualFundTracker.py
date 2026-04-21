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
from typing import Sequence

import aiohttp
import pytz
import ujson as json
from decorator_utils import check_connection_decorator
from decorator_utils import retry
from gdrive_tool import GDrive
from common_util import DesktopNotification

import logs.log_config as log_config  # pylint: disable=unused-import # import log  # bb # noqa: all
from models.day_change import InvestmentData, NavData, get_investment_data

from models import InvestmentHistory, OrderHistory, Units
from repository import (
    InvestmentHistoryRepository,
    OrderHistoryRepository,
    UnitsRepository,
    db_path,
)

try:
    import plotext as plt
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Installing requirements for you")
    os.system("pip3 install -r requirements.txt")
    import plotext as plt
    from rich.console import Console
    from rich.table import Table


download = False

INDIAN_TIMEZONE = pytz.timezone("Asia/Kolkata")
DATA_PATH = pathlib.Path(__file__).parent.resolve().joinpath("data")
lock_file = os.path.join(DATA_PATH, "lock_file.lock")
ICON_IMAGE = os.path.join(DATA_PATH, "icon.jpg")

# lock_manager = LockManager(lock_file)

FOLDER_NAME = "MutualFund"

investment_history_repo = InvestmentHistoryRepository()
order_history_repo = OrderHistoryRepository()
units_repo = UnitsRepository()

logging = logging.getLogger(__name__)


def round_up3(number: float) -> float:
    return round(number, 3)


def getfv(number: float) -> str:
    return (
        f"[green]+₹{round_up3(number)}[/green]"
        if number >= 0
        else f"[red]-₹{abs(round_up3(number))}[/red]"
    )


def get_colored_string_based_digit_being_positive_or_negative(
    string: str, number: float
) -> str:
    # return string in green color if number is positive else in red color
    string = f"[bold]{string}[/bold]"
    return f"[green]{string}[/green]" if number >= 0 else f"[red]{string}[/red]"


def getfp(percentage: float) -> str:
    return (
        f"[green]({round_up3(percentage)}%)[/green]"
        if percentage >= 0
        else f"[red]({round_up3(percentage)})%[/red]"
    )


async def writeToFileAsync(filename: pathlib.Path, data: dict, indent=4) -> None:
    logging.info("writing asynchronously to %s", filename)
    with open(file=filename, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)
    # async with GDrive(FOLDER_NAME) as gdrive:  // no profit of using events because we are using context managers, and it will trigger __aexit__ method
    #     gdrive.upload_event(filename)
    await GDrive(FOLDER_NAME).upload_async(filename)


def writeRawDataToFile(file_name: str, data: str) -> None:
    logging.info("writing raw string data to %s", file_name)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(data)


async def download_file(file_name: str) -> None:
    if download:
        logging.info("downloading file %s", file_name)
        await GDrive(FOLDER_NAME).download_async(file_name)


def writeToFile(file_name: pathlib.Path | str, data) -> None:
    logging.info("writing to a file asynchronously")
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def readJsonFile(filename: str | pathlib.Path):
    logging.info("reading fileName = %s ", filename)
    if not pathlib.Path(filename).exists() or download:
        GDrive(FOLDER_NAME).download(filename)
    with open(filename, "r", encoding="utf-8") as f:
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

        self.formatString = "%d-%b-%Y"
        self.dd_mm_yyyy = "%d-%m-%Y"
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
        self.past_nav_data: dict = {}
        logging.info("Initializing MutualFundTracker")
        logging.info("--Application has started---")
        logging.info("--Logged in as %s --", os.environ.get("USER"))

        self.logging = logging

        self.directoryString: str = pathlib.Path(__file__).parent.resolve().as_posix()
        self.sender_email: str = os.environ.get("shazmail")  # type: ignore
        self.password: str = os.environ.get("shazPassword")  # type: ignore

        self.dayChangeJsonFileString: pathlib.Path = DATA_PATH.joinpath(
            "dayChange.json"
        )
        self.dayChangeJsonFileStringBackupFile: pathlib.Path = DATA_PATH.joinpath(
            "dayChange_bkc.json"
        )

    async def initialize(self):
        logging.debug("----initializing----")

        day_change_tasks = asyncio.create_task(
            readJsonFileAsynchronously(self.dayChangeJsonFileString), name="daychange"
        )

        db_task = asyncio.create_task(download_file(db_path), name="db")

        results = await asyncio.gather(day_change_tasks, db_task)
        try:
            temp_data = results[0]
            self.json_data: InvestmentData = get_investment_data(temp_data)
        except (FileNotFoundError, JSONDecodeError):
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.run_once_initialization(None)
        self.unitsKeyList = units_repo.find_all_distinct_mfids()
        self.TableMutualFund = Table()
        self.summaryTable = Table()

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
        print(f"{nav_date_format=} {orderDateFormat=}")
        return orderDateFormat <= nav_date_format

    def check_for_current_date_investment_history_and_update_it(
        self,
        mfid: str,
        date_str: str,
        invested_amount: float,
        current_amount: float,
        day_change: float,
        nav: float | None,
        name: str = "",
        is_filled: bool = False,

    ) -> None:
        """
        Check if the current date is already in the investment history for the given MFID.
        If it is, update the invested and current amounts.
        """

        lastest_investment_history = (
            investment_history_repo.find_first_by_mfid_order_by_date_desc(mfid)
        )

        mf_name: str | None = (
            lastest_investment_history.mfname if lastest_investment_history else None
        )
        if name != "":
            mf_name = name

        date = datetime.strptime(date_str, self.formatString).date()
        existing_record = investment_history_repo.find_by_mfid_and_date(mfid, date)
        if existing_record:
            existing_record.invested_amount = invested_amount
            existing_record.current_amount = current_amount
            existing_record.day_change = day_change
            existing_record.nav = nav
            existing_record.is_filled = is_filled
            investment_history_repo.save(existing_record)
        else:
            new_record = InvestmentHistory(
                mfid=mfid,
                mfname=mf_name,
                date=date,
                invested_amount=invested_amount,
                current_amount=current_amount,
                day_change=day_change,
                nav=nav,
                is_filled=is_filled,
            )
            investment_history_repo.save(new_record)

            logging.info(
                "Saving investment history for %s on %s with invested amount %s and current amount %s",
                mf_name,
                date,
                invested_amount,
                current_amount,
            )

        if lastest_investment_history:
            latest_date = lastest_investment_history.date
            if date > latest_date:
                for i in range(1, (date - latest_date).days):
                    new_date = latest_date + timedelta(days=i)
                    new_record = InvestmentHistory(
                        mfid=lastest_investment_history.mfid,
                        mfname=lastest_investment_history.mfname,
                        date=new_date,
                        invested_amount=lastest_investment_history.invested_amount,
                        current_amount=lastest_investment_history.current_amount,
                        day_change=0.0,
                        nav=lastest_investment_history.nav,
                        is_filled=True,
                    )
                    investment_history_repo.save(new_record)

    def check_for_current_date_investment_history_and_update_it_for_all(self) -> None:
        """
        Check and update investment history for all mutual funds for the current date.
        """

        lastest_investment_history = (
            investment_history_repo.find_first_by_mfid_order_by_date_desc("ALL")
        )

        lastest_date = (
            lastest_investment_history.date
            if lastest_investment_history
            else datetime.now(INDIAN_TIMEZONE).date()
        )
        current_date = lastest_date
        while True:

            current_date = current_date + timedelta(days=1)

            invested_amount = 0.0
            current_amount = 0.0
            day_change = 0.0

            is_filled = False

            investment_histories: Sequence[InvestmentHistory] = (
                investment_history_repo.find_all_by_date(current_date)
            )
            if len(investment_histories) == len(self.unitsKeyList):
                for investment_history in investment_histories:
                    invested_amount += investment_history.invested_amount
                    current_amount += investment_history.current_amount
                    day_change += investment_history.day_change
                    is_filled = investment_history.is_filled
            else:
                logging.debug(
                    "Investment histories do not match the number of units. for date %s",
                    current_date,
                )
                return

            current_amount = round_up3(current_amount)

            day_change = round_up3(day_change)

            logging.debug(
                "Total invested amount: %s, Total current amount: %s, Total day change: %s for date %s",
                invested_amount,
                current_amount,
                day_change,
                current_date,
            )

            current_date_str = current_date.strftime(self.formatString)

            self.check_for_current_date_investment_history_and_update_it(
                "ALL",
                current_date_str,
                invested_amount,
                current_amount,
                day_change,
                None,
                "",
                is_filled,
            )

    # async def addToUnits(self, mutualfund_id, date, name: str) -> None:
    #     if mutualfund_id in self.Orders:
    #         keys = list(self.Orders[mutualfund_id].keys())
    #         for key in keys:
    #             print(f"date inside addToUnits = {key}")
    #             if  self.check_past_dates(date, key):

    #                 order_data = self.Orders[mutualfund_id].pop(key)
    #                 data = self.units[mutualfund_id]
    #                 data[0] += order_data[0]
    #                 data[1] += order_data[1]

    #                 logging.info(
    #                     "adding units: %s and amount: %s to units for %s",
    #                     order_data[0],
    #                     order_data[1],
    #                     name,
    #                 )

    #                 self.tasks.extend(
    #                     [
    #                         writeToFileAsync(self.unitsFile, self.units),  # type: ignore
    #                         writeToFileAsync(self.order_file, self.Orders),  # type: ignore
    #                     ]
    #                 )

    async def add_to_units_db(self, mfid: str, date: str) -> None:
        """
        Update the units database with unconsumed order histories for a given mutual fund ID up to a specified date.

        This method retrieves all unconsumed order histories associated with the provided mutual fund ID (`mfid`),
        and for each order, if its date is less than or equal to the specified `date`, it updates the units
        and total invested amounts in the units repository. It also marks the order as consumed and logs the update.
        The updated data is then uploaded asynchronously to Google Drive.

        Args:
            mfid (str): The mutual fund ID for which to update units.
            date (str): The cutoff date up to which order histories should be considered, in the format specified by `self.formatString`.
        Returns:
            None
        """

        dtime_date = datetime.strptime(date, self.formatString).date()

        order_histories: Sequence[OrderHistory] = (
            order_history_repo.find_all_by_mfid_and_consumed(mfid, False)
        )

        for order_history in order_histories:
            order_date = order_history.nav_date
            if order_date is not None and order_date <= dtime_date:

                unit_entity = units_repo.find_by_mfid(order_history.mfid)

                unit_entity.total_units += order_history.unit
                unit_entity.total_invested += order_history.amount
                units_repo.save(unit_entity)

                logging.info(
                    "Adding units: %s and amount: %s to units for %s",
                    order_history.unit,
                    order_history.amount,
                    order_history.mfname,
                )

                # Mark the order as consumed
                order_history.consumed = True
                order_history_repo.save(order_history)

                self.tasks.append(GDrive(FOLDER_NAME).upload_async(db_path))

    # async def addToUnitsNotPreExisting(self) -> None:
    #     """
    #     Adds new mutual fund units to the unit file.
    #     """
    #     for order_key in self.Orders:

    #         if order_key not in self.units and self.Orders[order_key]:
    #             self.units[order_key] = [0, 0]
    #             for date in self.Orders[order_key]:
    #                 date_data = self.Orders[order_key].pop(date)
    #                 self.units[order_key][0] += date_data[0]
    #                 self.units[order_key][1] += date_data[1]
    #                 logging.info(
    #                     "Adding new mf  units: %s and amount: %s to units for %s",
    #                     date_data[0],
    #                     date_data[1],
    #                     order_key,
    #                 )

    #             # Write the Units and Orders dictionaries to their respective files
    #             self.tasks.extend(
    #                 [
    #                     writeToFileAsync(self.unitsFile, self.units),  # type: ignore
    #                     writeToFileAsync(self.order_file, self.Orders),
    #                 ]
    #             )

    async def add_to_units_not_pre_existing(self) -> None:

        order_histories: Sequence[OrderHistory] = (
            order_history_repo.find_all_consumed_is(False)
        )
        for order_history in order_histories:
            if order_history.mfid not in self.unitsKeyList:

                unit_entity = Units(
                    mfid=order_history.mfid,
                    total_units=order_history.unit,
                    total_invested=order_history.amount,
                )
                units_repo.save(unit_entity)

                logging.info(
                    "Adding new mf units: %s and amount: %s to units for %s",
                    order_history.unit,
                    order_history.amount,
                    order_history.mfname,
                )

                # Mark the order as consumed
                order_history.consumed = True

                order_history_repo.save(order_history)

                self.tasks.append(GDrive(FOLDER_NAME).upload_async(db_path))

    def run_once_initialization(self, file) -> None:
        if not pathlib.Path.exists(DATA_PATH):
            pathlib.Path.mkdir(DATA_PATH)
        if file is not None:
            writeToFile(file, data=asdict(InvestmentData()))
        elif pathlib.Path.exists(self.dayChangeJsonFileStringBackupFile):
            backup_data = readJsonFile(self.dayChangeJsonFileStringBackupFile)
            writeToFile(self.dayChangeJsonFileString, backup_data)
            self.json_data = get_investment_data(backup_data)  # type: ignore
        else:
            writeToFile(
                self.dayChangeJsonFileStringBackupFile, asdict(InvestmentData())
            )
            self.json_data = InvestmentData()

    def initializeTables(self) -> None:
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
        # self.TableMutualFund.add_column("LAST UPDDATED", justify="center")

    def summary_table_edit(self) -> None:
        try:

            latest_date_nav = investment_history_repo.find_latest_nav_date()

            all_inv_his_latest = list(
                filter(
                    lambda x: x.mfid != "ALL",
                    investment_history_repo.find_latest_records_for_all_mfids(),
                )
            )

            invested = 0.0
            current = 0.0
            total_day_change = 0.0
            latest_date: datetime = all_inv_his_latest[0].updated_at

            for latest_investment_history in all_inv_his_latest:
                if latest_investment_history.updated_at > latest_date:
                    latest_date = latest_investment_history.updated_at

                current += latest_investment_history.current_amount
                invested += latest_investment_history.invested_amount
                total_day_change += latest_investment_history.day_change if latest_investment_history.date == latest_date_nav else 0.0

                unconsumed_order_histories = order_history_repo.find_all_by_mfid_and_consumed(latest_investment_history.mfid, False)

                for unconsumed_order_history in unconsumed_order_histories:
                    if unconsumed_order_history.consumed == 0:
                        current += unconsumed_order_history.amount
                        invested += unconsumed_order_history.amount

            current = round(current, 3)

            lastUpdated = latest_date.strftime(self.formatString + " %X")

            totalProfit = current - invested
            totalProfitPercentage = totalProfit / invested * 100

            Investment_history_second_latest_by_nav_date = (
                investment_history_repo.find_second_latest_by_mfid("ALL")
            )

            current_amount_second_latest_by_nav_date = (
                Investment_history_second_latest_by_nav_date.current_amount
                if Investment_history_second_latest_by_nav_date
                else invested
            )

            total_day_change_percentage = (
                total_day_change / current_amount_second_latest_by_nav_date * 100
            )

            logging.debug(
                "Total Profit: %s, Total Profit Percentage: %s, Total Day Change: %s, Total Day Change Percentage: %s",
                totalProfit,
                totalProfitPercentage,
                total_day_change,
                total_day_change_percentage,
            )

        except Exception as err:
            print(str(err))
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
        dailyReturnString = f"[yellow]•[/yellow][bold]{getfv(total_day_change)} {getfp(total_day_change_percentage)}[/bold]"
        lastUpdatedString = f"Last Updated\n\n[b][yellow]{lastUpdated}[/yellow][/b]"
        self.summaryTable.add_row(
            investedString,
            currentString,
            totalReturnString + "\n" + dailyReturnString,
            lastUpdatedString,
        )

    def MutualFundTableEdit(self, id_: str) -> None:
        try:

            latest_investment_history: InvestmentHistory = (
                investment_history_repo.find_first_by_mfid_order_by(id_, "date", "desc")
            )
            second_latest_investment_history = (
                investment_history_repo.find_second_latest_by_mfid(id_)
            )
            current_amount_second_latest_by_nav_date = (
                second_latest_investment_history.current_amount
                if second_latest_investment_history
                else latest_investment_history.invested_amount
            )

            SchemeName = latest_investment_history.mfname
            dayChange = (
                latest_investment_history.day_change
                if latest_investment_history.day_change
                else 0
            )
            current = latest_investment_history.current_amount
            invested = latest_investment_history.invested_amount
            date = latest_investment_history.date.strftime(self.formatString)
            nav = latest_investment_history.nav
            updated_at = latest_investment_history.updated_at.strftime(
                self.formatString + " %X"
            )

            unconsumed_order_histories = order_history_repo.find_all_by_mfid_and_consumed(latest_investment_history.mfid, False)

            for unconsumed_order_history in unconsumed_order_histories:
                if unconsumed_order_history.consumed == 0:
                    current += unconsumed_order_history.amount
                    invested += unconsumed_order_history.amount
                print("in the unconsumed block")

            logging.debug(
                "Retrieved values - Scheme Name: %s, Day Change: %s, Current: %s, Invested: %s, Date: %s, Updated At: %s",
                SchemeName,
                dayChange,
                current,
                invested,
                date,
                updated_at,
            )
        except KeyError:
            self.console.print(
                # type: ignore
                "Incomplete info in Json file try[yellow][b]-d y[/yellow][/b] option"
            )
            exit(256)
        except Exception as error_occurred:
            self.console.print(error_occurred.__cause__)

            exit(256)

        dayChangePercentage: float = round_up3(
            dayChange / current_amount_second_latest_by_nav_date * 100
        )
        dayChangeString = f"{dayChangePercentage}%\n\n[b]{getfv(dayChange)}[/b]"

        returns = round_up3(current - invested)

        returnsPercentage = returns / invested * 100

        returnString = f"₹{returns}\n\n[b]{getfp(returnsPercentage)}[/b]"
        currentString = f"₹{current}\n\n[b]₹{invested}[/b]"
        nav_date = f"[yellow]{date}[/yellow]\n\n[b]{nav}[/b]"
        schemeName = get_colored_string_based_digit_being_positive_or_negative(
            SchemeName, current - invested
        )
        # lastUpdated = f"[cyan][b]{updated_at.split(' ')[0]}[/b][/cyan]\n\n[bright_cyan][b]{updated_at.split(' ')[1]}[/b][/bright_cyan]"

        self.TableMutualFund.add_row(
            schemeName, dayChangeString, returnString, currentString, nav_date
        )

    def dayChangeTableAll(self, dic: dict) -> None:
        all_daily_table = Table(title="Day Change Total", show_lines=True, expand=True)
        all_daily_table.add_column("NAV", justify="center", no_wrap=True)
        all_daily_table.add_column("DayChange", justify="center", no_wrap=True)
        sum_changed_sorted_keys = sorted(
            dic.keys(), key=lambda x: datetime.strptime(x, "%d-%b-%Y")
        )
        dic = {k: dic[k] for k in sum_changed_sorted_keys}

        nav_col = ""
        dayChange_col = ""

        for nav, dayChange in dic.items():
            nav_col += f"[yellow]{nav}[/yellow]\n"
            dayChange_col += f"{getfv(dayChange)}\n"
        all_daily_table.add_row(nav_col, dayChange_col)
        self.console.print(all_daily_table)

        print(end="\n\n")
        dates: list = sum_changed_sorted_keys
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
        self.unitsKeyList = units_repo.find_all_distinct_mfids()

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
            unit_entity = units_repo.find_by_mfid(key)
            units: float = unit_entity.total_units
            nav_col = ""
            changed_col = ""
            i = True
            prev_day_change = 0.0

            for nav, day_change in value.items():
                if i:
                    prev_day_change = units * day_change
                    i = False
                    continue
                day_change *= units
                day_change_data: float = round(day_change - prev_day_change, 3)

                if nav in sum_day_change:
                    sum_day_change[nav] += day_change_data
                else:
                    sum_day_change[nav] = day_change_data
                nav_col += f"[yellow]{nav}[/yellow]\n"

                changed_col += f"{getfv(day_change_data)}\n"
                prev_day_change = day_change

            daily_table.add_row(name, nav_col, changed_col)

        if not self.console:
            self.console = Console()
        print("\n")
        self.console.print(daily_table)
        print("\n")
        self.dayChangeTableAll(sum_day_change)

    def draw_table(self):
        self.initializeTables()
        self.console = Console()
        self.summary_table_edit()
        self.console.print(self.summaryTable)
        self.UpdateKeyList()
        sortedKeys = sorted(
            self.json_data.funds.keys(),
            key=lambda x: self.json_data.funds[x]["invested"],
            reverse=True,
        )
        for ids in sortedKeys:
            self.MutualFundTableEdit(ids)
        self.console.print(self.TableMutualFund)

    def get_grep_string(self) -> str:
        unitKeyList = self.unitsKeyList

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

    @staticmethod
    def draw_graph_current_vs_invested() -> None:
        print()
        data: Sequence[InvestmentHistory] = investment_history_repo.find_all_by_mfid(
            "ALL"
        )

        dates: list = []
        invested_amounts: list = []
        current_amounts: list = []
        d = 0

        for entry in data:
            d += 1
            dates.append(d)
            invested_amounts.append(entry.invested_amount)
            current_amounts.append(entry.current_amount)

        plt.plot_size(100, 30)
        plt.title("Current vs Invested Amount")

        plt.ylabel("Amount", yside="left")
        plt.plot(dates, invested_amounts, color="blue", label="Invested Amount")
        plt.plot(dates, current_amounts, color="green", label="Current Amount")

        plt.clear_color()
        plt.show()
        plt.clear_figure()

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
            DesktopNotification(
                "Mutual Fund Tracker",
                f"Updated at {lastUpdated}",
                icon_image=ICON_IMAGE,
            )

        return True

    @check_connection_decorator
    @retry(retries=3, delay=1, fail_after_retry_exhausted=True)
    async def download_all_nav_file(self) -> bool:

        logging.info("--downloading the NAV file from server--")

        async with aiohttp.client.ClientSession(raise_for_status=True) as client:
            start_time = time.time()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.amfiindia.com/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            res = await client.get(
                "https://www.amfiindia.com/spages/navopen.txt",
                timeout=10,
                headers=headers,
                raise_for_status=True,
            )
            status = res.status
            text = await res.text()

            if status != 200:
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

        await self.add_to_units_db(ids, prev_day_nav_date)
        units_entity = units_repo.find_by_mfid(ids)
        units: float = units_entity.total_units

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
            if key.isnumeric() and key not in self.unitsKeyList:
                del self.json_data.funds[key]

        self.tasks.append(
            writeToFileAsync(self.dayChangeJsonFileString, asdict(self.json_data))
        )

    async def read_my_nav_file(self) -> tuple[int, int, int, str | None]:
        """
        returns subtotal, total_invested , totaldaychange
        """

        sum_total = 0
        total_invested = 0
        total_day_change = 0
        latest_date = None
        for line in self.nav_my_file.splitlines():
            print(line)
            temp = line.strip().split(";")
            _id, name, nav, date = (
                temp[0],
                temp[3].split("-")[0].strip(),
                float(temp[4]),
                temp[5],
            )
            latest_date = date

            # type: ignore
            dayChange: float = await self.day_change_method(_id, nav, date, name)

            unit_entity = units_repo.find_by_mfid(_id)

            current = round(unit_entity.total_units * nav, 3)
            invested = unit_entity.total_invested
            sum_total += current
            total_invested += invested
            if dayChange != -1:
                total_day_change += dayChange

            cur_json_id = self.json_data.funds[_id]
            cur_json_id.latestNavDate = date
            cur_json_id.current = current
            cur_json_id.invested = invested
            cur_json_id.dayChange = dayChange
            self.check_for_current_date_investment_history_and_update_it(
                _id, date, invested, current, dayChange, nav, name
            )

        return sum_total, total_invested, total_day_change, latest_date

    async def get_current_values(self) -> None:

        logging.info("--Main calculation--")
        if self.is_downloadable:
            await self.add_to_units_not_pre_existing()
            if not await self.download_all_nav_file():
                return

            if not await self.update_my_nav_file():  # type: ignore
                return

        sum_total, total_invested, total_day_change, latest_date = (
            await self.read_my_nav_file()
        )

        total_profit = sum_total - total_invested
        total_profit_percentage = total_profit / total_invested * 100

        total_profit_percentage = round(total_profit_percentage, 3)
        total_profit = round(total_profit, 3)
        total_day_change = round(total_day_change, 3)

        self.json_data.totalProfit = total_profit
        self.json_data.sumTotal = round(sum_total, 3)
        self.json_data.totalInvested = total_invested
        self.json_data.totalProfitPercentage = total_profit_percentage

        self.json_data.total_day_change = total_day_change

        self.check_for_current_date_investment_history_and_update_it_for_all()

        self.tasks.append(
            writeToFileAsync(self.dayChangeJsonFileString, data=asdict(self.json_data))
        )
        self.tasks.append(GDrive(FOLDER_NAME).upload_async(db_path))

    async def del_cleanup(self):
        """

        :return:
        """
        if self.tasks:
            start_time = time.time()

            await asyncio.gather(*self.tasks)

            logging.debug(
                f"---Took {(time.time() - start_time):.2f} Secs to complete the tasks---"
            )
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

        tracker.draw_graph_current_vs_invested()


if __name__ == "__main__":
    from repository import create_db_and_tables

    create_db_and_tables()
    start = time.time()
    import cProfile

    cProfile.run(
        statement="asyncio.run(main2())", sort="cumtime", filename="profile.out"
    )
