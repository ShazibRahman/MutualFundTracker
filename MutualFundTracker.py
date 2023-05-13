import hashlib
import json
import logging
import os
import pathlib
import re
import sys
import time
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import Tuple

import pytz
import requests

sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())


from gdrive.GDrive import GDrive  # autopep8: off

INDIAN_TIMEZONE = pytz.timezone('Asia/Kolkata')
DATA_PATH = pathlib.Path(__file__).parent.resolve().joinpath('data').as_posix()
FOLDER_NAME = "MutualFund"

try:
    import plotext as plt
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print('Installing requirements for you')
    os.system('pip3 install -r requirements.txt')
    import plotext as plt
    from rich.console import Console
    from rich.table import Table

LOGGER_PATH = pathlib.Path(DATA_PATH).resolve().joinpath(
    'logger.log').as_posix()

logging.basicConfig(filename=LOGGER_PATH,
                    filemode='a',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

gdrive: GDrive = GDrive(FOLDER_NAME,logging)


def roundUp3(number: float) -> float:
    return round(number, 3)


def getfv(number: float) -> str:
    return f'[green]+₹{roundUp3(number)}[/green]' if number >= 0 else f'[red]-₹{abs(roundUp3(number))}[/red]'


def getfp(percentage: float) -> str:
    return f'[green]({roundUp3(percentage)}%)[/green]' if percentage >= 0 else f'[red]({roundUp3(percentage)})%[/red]'


def writeToFile(filename: str, data: object, indent=4) -> None:
    logging.info(f"writing to {filename=}")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=indent)
    gdrive.upload(filename)


def writeRawDataToFile(file_name: str, data: str) -> None:
    logging.info(f"writing raw string data to {file_name}")
    with open(file_name, 'w') as file:
        file.write(data)


def readJsonFile(filename: str):
    logging.info(f"reading {filename=}")
    gdrive.download(filename)
    with open(filename, 'r') as f:
        return json.load(f)


class MutualFund:

    def __init__(self) -> None:
        logging.info("Initializing MutualFundTracker")
        logging.info("--Application has started---")
        logging.info(f"--Logged in as {os.environ.get('USER')}")

        self.logging = logging

        self.directoryString: str = pathlib.Path(
            __file__).parent.resolve().as_posix()
        self.sender_email: str = os.environ.get("shazmail")  # type: ignore
        self.password: str = os.environ.get("shazPassword")  # type: ignore

        self.navallfile: None
        self.orderfile: str = pathlib.Path(
            DATA_PATH).resolve().joinpath('order.json').as_posix()
        self.navMyfile: None
        self.dayChangeJsonFileString: str = pathlib.Path(
            DATA_PATH).resolve().joinpath('dayChange.json').as_posix()
        self.dayChangeJsonFileStringBackupFile: str = self.dayChangeJsonFileString + ".bak"
        self.unitsFile: str = pathlib.Path(
            DATA_PATH).resolve().joinpath('units.json').as_posix()
        try:
            self.Units: dict = readJsonFile(self.unitsFile)
        except JSONDecodeError:
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.Units = {}
            self.runOnceInitialization(self.unitsFile)
        try:
            self.Orders: dict = readJsonFile(self.orderfile)
        except JSONDecodeError:
            print("Something went wrong with the order file")
            self.Orders = {}
            self.runOnceInitialization(self.orderfile)

        if not self.Units:
            print(
                f'No mutual Fund specified to track please Add something in {self.unitsFile} file to track'
            )
            exit(0)

        try:
            self.jsonData: dict = readJsonFile(self.dayChangeJsonFileString)
        except FileNotFoundError:
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.runOnceInitialization(None)
        except JSONDecodeError:
            self.runOnceInitialization(None)

        self.unitsKeyList = list(self.Units.keys())
        self.console = None
        self.TableMutualFund = None
        self.summaryTable = None
        self.formatString = "%d-%b-%Y"
        plt.datetime.set_datetime_form(date_form=self.formatString)

    def checkPastdates(self, NavDate: str, orderDate) -> bool:
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
        nav_date_foramt = datetime.strptime(NavDate, self.formatString)
        orderDateFormat = datetime.strptime(orderDate, self.formatString)
        return orderDateFormat <= nav_date_foramt

    def addToUnits(self, mfid, date) -> None:
        found = False
        if self.Orders.__contains__(mfid):
            keys_list = list(self.Orders[mfid].keys())
            if len(keys_list) > 0:
                for key in keys_list:
                    if self.checkPastdates(date, key):
                        order_data = self.Orders[mfid].pop(date)
                        data = self.Units[mfid]
                        data[0] += order_data[0]
                        data[1] += order_data[1]
                        found = True
        if found:
            writeToFile(self.unitsFile, self.Units)
            writeToFile(self.orderfile, self.Orders)
        else:
            logging.info(
                f"--No new Orders were found for {self.jsonData[mfid]['name']}--"
            )

    def addToUnitsNotPreEXisting(self) -> None:
        logging.info("--adding new MF units to Unit file")
        key_list = list(self.Orders.keys())
        found = False
        for i in key_list:
            found = False
            if i not in self.Units:
                found = True
                self.Units[i] = [0, 0]
                date_list = list(self.Orders[i].keys())
                for date in date_list:
                    date_data = self.Orders[i].pop(date)
                    self.Units[i][0] += date_data[0]
                    self.Units[i][1] += date_data[1]

                writeToFile(self.unitsFile, self.Units)
                writeToFile(self.orderfile, self.Orders)
        if len(key_list) == 0 or not found:
            logging.info("--No new Mutual fund was found in Order--")

    def addOrder(self, MFID, unit, amount, date) -> None:
        """
        mfid , unit : float , amount :float , date : for ex 07-May-2022
        """
        logging.info("--adding order to Unit file--")
        if self.Orders.__contains__(MFID) and self.Orders[MFID].__contains__(
                date):
            data = self.Orders[MFID][date]
            data[0] += unit
            data[1] += amount
        elif self.Orders.__contains__(MFID):
            self.Orders[MFID][date] = [unit, amount]
        else:
            self.Orders[MFID] = {}
            self.Orders[MFID][date] = [unit, amount]
        logging.info(
            f"--Adding  Units={unit}, amount={amount}, date={date} to {self.jsonData[MFID]['name']}--"
        )
        writeToFile(self.orderfile, self.Orders)

    def runOnceInitialization(self, file):
        if not pathlib.Path.exists(DATA_PATH):
            pathlib.Path.mkdir(DATA_PATH)
        if file is not None:
            writeToFile(file, {})
        else:
            if pathlib.Path.exists(self.dayChangeJsonFileStringBackupFile):
                backup_data = readJsonFile(
                    self.dayChangeJsonFileStringBackupFile)
                writeToFile(self.dayChangeJsonFileString, backup_data)
                self.jsonData = backup_data
            else:
                writeToFile(self.dayChangeJsonFileStringBackupFile, {})
                self.jsonData = {}

    def initializeTables(self) -> None:
        if len(self.unitsKeyList) == 0:
            print('no Mutual Fund found')
            exit()
        self.TableMutualFund = Table(
            expand=True,
            show_lines=True,
        )
        self.summaryTable = Table.grid(expand=True, pad_edge=True, padding=2)

        self.summaryTable.add_column('invested',
                                     justify='center',
                                     no_wrap=True)
        self.summaryTable.add_column('current',
                                     justify='right',
                                     no_wrap=True)
        self.summaryTable.add_column('total returns',
                                     justify='right',
                                     no_wrap=True)
        self.summaryTable.add_column('lastUpdated',
                                     justify='right',
                                     no_wrap=True)

        self.TableMutualFund.add_column('SCHEME NAME', justify='center')
        self.TableMutualFund.add_column('DAY CHANGE', justify='center')
        self.TableMutualFund.add_column('RETURNS', justify='center')
        self.TableMutualFund.add_column('CURRENT', justify='center')
        self.TableMutualFund.add_column('NAV', justify='center')

    def summaryTableEdit(self) -> None:
        try:
            lastUpdated = self.jsonData['lastUpdated']
            current = self.jsonData['sumTotal']
            invested = self.jsonData['totalInvested']
            totalProfitPercentage = self.jsonData['totalProfitPercentage']
            totalProfit = self.jsonData['totalProfit']
            totalDaychange = self.jsonData['totalDaychange']
            totalDaychangePercentage = totalDaychange / invested * 100
        except KeyError:
            self.console.print(
                'Incomplete info in Json file try [b][yellow]-d y[/yellow][/b] option'
            )
            exit()

        investedString = f'Invested\n\n[bold]₹{invested}[/bold]'
        currentColor = f'[green]₹{current}[/green]' if current >= invested else f'[red]₹{current}[/red]'
        currentString = f'Current\n\n[bold]{currentColor}[/bold]'
        totalReturnString = f'[yellow]•[/yellow]Total Returns\n\n[bold]{getfv(totalProfit)} {getfp(totalProfitPercentage)}[/bold]'
        dailyReturnString = f'[yellow]•[/yellow][bold]{getfv(totalDaychange)} {getfp(totalDaychangePercentage)}[/bold]'
        lastUpdatedString = f'Last Updated\n\n[b][yellow]{lastUpdated}[/yellow][/b]'
        self.summaryTable.add_row(investedString, currentString,
                                  totalReturnString + "\n" + dailyReturnString, lastUpdatedString)

    def MutualFundTableEdit(self, id_: str) -> None:
        try:
            preMF = self.jsonData[id_]
            SchemeName = preMF['name']
            dayChange = preMF['dayChange']
            current = preMF['current']
            invested = preMF['invested']
            date = preMF['latestNavDate']
        except KeyError:
            self.console.print(
                'Incomplete info in Json file try[yellow][b]-d y[/yellow][/b] option'
            )
            exit(256)
        except Exception:
            self.console.print('Something went wrong')

            exit(256)
        if dayChange != 'N.A.':
            dayChangePercentage: float = roundUp3(dayChange / invested * 100)
            dayChangeString = f'{dayChangePercentage}%\n\n[b]{getfv(dayChange)}[/b]'
        else:
            dayChangeString = 'N.A.\n\n[b]N.A.[/b]'

        returns = roundUp3(current - invested)

        returnsPercentage = returns / invested * 100

        returnString = f'₹{returns}\n\n[b]{getfp(returnsPercentage)}[/b]'
        currentString = f'₹{current}\n\n[b]₹{invested}[/b]'
        nav_date = f'[yellow]{date}[/yellow]\n\n[b]{preMF["nav"][date]}[/b]'

        self.TableMutualFund.add_row(SchemeName, dayChangeString, returnString,
                                     currentString, nav_date)

    def dayChangeTableAll(self, dic: dict) -> None:
        all_daily_table = Table(title='Day Change Total',
                                show_lines=True,
                                expand=True)
        all_daily_table.add_column('NAV', justify='center', no_wrap=True)
        all_daily_table.add_column('DayChange', justify='center', no_wrap=True)
        sum_daychange_sorted_keys = sorted(
            dic.keys(), key=lambda x: datetime.strptime(x, '%d-%b-%Y'))
        dic = {k: dic[k] for k in sum_daychange_sorted_keys}

        nav_col = ''
        dayChange_col = ''

        for nav, dayChange in dic.items():
            nav_col += f'[yellow]{nav}[/yellow]\n'
            dayChange_col += f'{getfv(dayChange)}\n'
        all_daily_table.add_row(nav_col, dayChange_col)
        self.console.print(all_daily_table)

        print(end="\n\n")
        dates: list = sum_daychange_sorted_keys
        dayChangeList: list = list(dic.values())
        plt.clear_figure()
        plt.plot_size(100, 30)
        plt.title('Day Change')
        plt.xlabel('Date', xside='upper')
        plt.ylabel('profit', yside='left')

        plt.plot_date(dates,
                      dayChangeList,
                      color='green',
                      label='DayChange Plot')
        plt.clear_color()
        plt.show()

    def UpdateKeyList(self):
        self.unitsKeyList = self.Units.keys()

    def DayChangeTable(self):
        logging.info("--rendering day change table--")
        daily_table = Table(title='Day Change table',
                            show_lines=True,
                            expand=True)
        daily_table.add_column('SCHEME NAME', justify='center', no_wrap=True)
        daily_table.add_column('NAV', justify='center', no_wrap=True)
        daily_table.add_column('DayChange', justify='center', no_wrap=True)

        sumDayChange: dict = {}
        self.UpdateKeyList()
        for key in self.unitsKeyList:
            if not self.jsonData.__contains__(key):
                self.getCurrentValues(False)
            value: dict[str, float] = self.jsonData[key]['nav']
            name: str = self.jsonData[key]['name']
            units: float = self.Units[key][0]
            nav_col = ''
            daychange_col = ''
            i = True
            prevdayChange = 0.0

            for nav, daychange in value.items():
                if i:
                    prevdayChange = units * daychange
                    i = False
                    continue
                daychange: float = units * daychange
                daychangeData: float = round(daychange - prevdayChange, 3)

                if nav in sumDayChange:
                    sumDayChange[nav] += daychangeData
                else:
                    sumDayChange[nav] = daychangeData
                nav_col += f'[yellow]{nav}[/yellow]\n'

                daychange_col += f'{getfv(daychangeData)}\n'
                prevdayChange = daychange

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

        grepSearchString = ''

        for i in range(len(unitKeyList)):
            if i == 0:
                grepSearchString += unitKeyList[i]
            else:
                grepSearchString += '|' + unitKeyList[i]

        return grepSearchString

    def drawGraph(self) -> None:
        for ids in self.unitsKeyList:
            value = self.jsonData[ids]
            print()
            x = value['nav'].keys()
            y = value['nav'].values()
            plt.plot_size(100, 30)
            plt.title(value['name'])
            plt.xlabel('Date', xside='upper')
            plt.ylabel('profit', yside='left')

            plt.plot_date(x, y, color='green', label='Nav Plot')
            plt.clear_color()

            plt.show()
            plt.clear_figure()
        print()

    def updateMyNaVFile(self):
        if self.navallfile is None:
            if not self.downloadAllNavFile():
                return False

        result = ""
        pattern = self.getGrepString()
        for i in self.navallfile.splitlines():
            if re.search(pattern, i):

                result += i.strip()+"\n"

        self.navMyfile = result
        if self.jsonData.__contains__("hash2"):
            new_hash = hashlib.md5(self.navMyfile.encode()).hexdigest()
            prev_hash = self.jsonData['hash2']
            if prev_hash == new_hash:
                logging.info("--Nothing to update--")
                return False
            self.jsonData['hash2'] = new_hash
            lastUpdated = datetime.now(INDIAN_TIMEZONE).strftime(
                self.formatString + " %X")
            self.jsonData['lastUpdated'] = lastUpdated
            writeToFile(self.dayChangeJsonFileStringBackupFile,
                        readJsonFile(self.dayChangeJsonFileString))
        return True

    def downloadAllNavFile(self) -> bool:
        logging.info("--downloading the NAV file from server--")
        start = time.time()
        try:
            res = requests.get("https://www.amfiindia.com/spages/NAVopen.txt")
            if res.status_code != 200:
                return False
        except:
            return False

        else:
            self.navallfile = res.text
            logging.info(
                f"--took {(time.time() - start):.2f} Secs to download the file")
            new_hash = hashlib.md5(self.navallfile.encode()).hexdigest()
            if self.jsonData.__contains__('hash'):
                prev_hash = self.jsonData['hash']
                if prev_hash == new_hash:
                    logging.info("--No changes found in the new NAV file--")
                    return False
            self.jsonData['hash'] = new_hash

            return True

    def dayChangeMethod(self, ids: str, todayNav: float, latestNavDate: str,
                        name: str) -> str | float:

        dayChange = 0.0
        self.isExistingId(ids, name, latestNavDate, todayNav)
        data: dict[str:str] = self.jsonData[ids]['nav']
        latestDate = datetime.strptime(latestNavDate, self.formatString)

        prevDayNavDate: str = datetime.strftime(latestDate - timedelta(1),
                                                self.formatString)

        if prevDayNavDate not in data:
            key_list = list(data.keys())
            length = len(key_list)
            if length == 0:
                data[latestNavDate] = todayNav
                return 'N.A.'
            elif length == 1 and key_list[-1] == latestNavDate:
                return 'N.A.'
            elif key_list[-1] == latestNavDate:
                prevDayNavDate = key_list[-2]
            else:
                prevDayNavDate = key_list[-1]

        self.addToUnits(ids, prevDayNavDate)
        units: float = self.Units[ids][0]

        prevDaySum: float = data[prevDayNavDate] * units
        dayChange: float = round(todayNav * units - prevDaySum, 3)
        self.jsonData[ids]['dayChange'] = dayChange
        data[latestNavDate] = todayNav
        return dayChange

    def isExistingId(self, ids: str, name: str, latestNavDate: str,
                     todayNav: float) -> None:
        if not self.jsonData.__contains__(ids):
            self.jsonData[ids] = {}
            self.jsonData[ids]['name'] = name
            self.jsonData[ids]['nav'] = {}
            self.jsonData[ids]['nav'][latestNavDate] = todayNav
            self.jsonData[ids]['latestNavDate'] = latestNavDate

    def cleanUp(self) -> None:
        keys:list[str] = list(self.jsonData.keys())
        for key in keys:
            if key.isnumeric() and key not in self.Units:
                del self.jsonData[key]

        writeToFile(self.dayChangeJsonFileString, self.jsonData)

    def readMyNavFile(self) -> Tuple[float, float, float]:
        """
        returns subtotal, totalInvested , totaldaychange
        """

        sumTotal = 0
        totalInvested = 0
        totalDayChange = 0

        for line in self.navMyfile.splitlines():
            current = 0
            dayChange = 0

            temp = line.strip().split(";")
            _id, name, nav, date = temp[0], temp[3].split(
                '-')[0].strip(), float(temp[4]), temp[5]

            dayChange = self.dayChangeMethod(_id, nav, date, name)

            current = round(self.Units[_id][0] * nav, 3)
            invested = self.Units[_id][1]
            sumTotal += current
            totalInvested += invested
            if dayChange != 'N.A.':
                totalDayChange += dayChange

            cur_json_id: dict = self.jsonData[_id]
            cur_json_id['latestNavDate'] = date
            cur_json_id['current'] = current
            cur_json_id['invested'] = invested
            cur_json_id['dayChange'] = dayChange
        return sumTotal, totalInvested, totalDayChange

    def getCurrentValues(self, download: bool) -> None:
        logging.info("--Main calculation--")
        if download:
            self.addToUnitsNotPreEXisting()
            if not self.downloadAllNavFile():
                return

            if not self.updateMyNaVFile():
                return

        sumTotal, totalInvested, totalDaychange = self.readMyNavFile()

        totalProfit = sumTotal - totalInvested
        totalProfitPercentage = totalProfit / totalInvested * 100

        totalProfitPercentage = round(totalProfitPercentage, 3)
        totalProfit = round(totalProfit, 3)
        totalDaychange = round(totalDaychange, 3)
        self.jsonData['totalProfit'] = totalProfit
        self.jsonData['sumTotal'] = round(sumTotal, 3)
        self.jsonData['totalInvested'] = totalInvested
        self.jsonData['totalProfitPercentage'] = totalProfitPercentage
        self.jsonData['totalDaychange'] = totalDaychange

        writeToFile(self.dayChangeJsonFileString, self.jsonData)


if __name__ == "__main__":
    tracker = MutualFund()
    tracker.getCurrentValues(download=True)
    tracker.drawTable()
