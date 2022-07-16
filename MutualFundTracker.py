import logging
import hashlib
import time

try:
    import json
    from datetime import datetime, timedelta
    from json.decoder import JSONDecodeError
    from rich.console import Console
    from rich.table import Table
    import os
    import plotext as plt
except Exception as e:
    print('''please go to the project folder and run this commmand 
    'pip install -r requirements.txt'
    ''')
    print(e)
    exit()
logging.basicConfig(filename=os.path.dirname(__file__) + '/data/logger.log',
                    filemode='a',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


def roundUp3(number: float) -> float:
    return round(number, 3)


def getfv(number: float) -> str:
    return f'[green]+₹{roundUp3(number)}[/green]' if number >= 0 else f'[red]-₹{abs(roundUp3(number))}[/red]'


def getfp(percentage: float) -> str:
    return f'[green]({roundUp3(percentage)}%)[/green]' if percentage >= 0 else f'[red]({roundUp3(percentage)})%[/red]'


class MutualFund:

    def __init__(self) -> None:
        logging.info("--Application has started---")
        logging.info(f"--Logged in as {os.environ.get('USER')}")
        self.directoryString = os.path.dirname(__file__)

        self.navallfile: str = self.directoryString + "/data/NAVAll.txt"
        self.orderfile: str = self.directoryString + "/data/order.json"
        self.navMyfile = self.directoryString + "/data/nav.txt"
        self.dayChangeJsonFileString = self.directoryString + "/data/dayChange.json"
        self.dayChangeJsonFileStringBackupFile = self.dayChangeJsonFileString + ".bak"
        self.unitsFile = self.directoryString + "/data/units.json"
        try:
            self.Units = json.load(open(self.unitsFile))
        except:
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.Units = {}
            self.runOnceInitialization(self.unitsFile)
        try:
            self.Orders: dict = json.load((open(self.orderfile)))
        except:
            self.Orders = {}
            self.runOnceInitialization(self.orderfile)

        if not self.Units:
            print(
                f'No mutual Fund specified to track please Add something in {self.unitsFile} file to track'
            )
            exit()

        try:
            self.jsonData = json.load(open(self.dayChangeJsonFileString))
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

    def writeToFile(self, filePath, Jsondata):
        logging.info(f"--writing to file {filePath}--")
        with open(filePath, 'w') as outfile:
            json.dump(Jsondata, outfile, indent=4)

    def checkPastdates(self, NavDate: str, orderDate):
        '''
        to check whether the order date is equal or smaller than the (nav date - 1)
        orders date = 13-may
        nav -1 date = 13-may
        in this case the orders should move to units

        scenario 2 

        order date = 12-May
        nav - 1 date = 13-May

        in this case orders should move to units file
        '''
        NavDateForamt = datetime.strptime(NavDate, self.formatString)
        orderDateFormat = datetime.strptime(orderDate, self.formatString)
        return orderDateFormat <= NavDateForamt

    def addToUnits(self, mfid, date):
        found = False
        if self.Orders.__contains__(mfid):
            keys_list = list(self.Orders[mfid].keys())
            if len(keys_list) > 0:
                for key in keys_list:
                    if self.checkPastdates(date, key):
                        OrderData = self.Orders[mfid].pop(date)
                        data = self.Units[mfid]
                        data[0] += OrderData[0]
                        data[1] += OrderData[1]
                        found = True
        if found:
            self.writeToFile(self.unitsFile, self.Units)
            self.writeToFile(self.orderfile, self.Orders)
        if not found:
            logging.info(
                f"--No new Orders were found for {self.jsonData[mfid]['name']}--"
            )

    def addToUnitsNotPreEXisting(self):
        logging.info("--adding new MF units to Unit file")
        key_list = list(self.Orders.keys())
        found = False
        for i in key_list:
            found = False
            if i not in self.Units:
                found = True
                self.Units[i] = [0, 0]
                dateList = list(self.Orders[i].keys())
                for date in dateList:
                    dateData = self.Orders[i].pop(date)
                    self.Units[i][0] += dateData[0]
                    self.Units[i][1] += dateData[1]

                self.writeToFile(self.unitsFile, self.Units)
                self.writeToFile(self.orderfile, self.Orders)
        if len(key_list) == 0 or not found:
            logging.info("--No new Mutual fund was found in Order--")

    def searchMutualFund(self, string: str):
        os.system(f'''
        grep -wi '{string}' {self.navallfile} 

        ''')

    def addOrder(self, MFID, unit, amount, date):
        '''
        mfid , unit : float , amount :float , date : for ex 07-May-2022
        '''
        logging.info(f"--adding order to Unit file--")
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
        self.writeToFile(self.orderfile, self.Orders)

    def runOnceInitialization(self, file):
        if not os.path.isdir(self.directoryString + '/data'):
            os.system(f'''mkdir {self.directoryString+"/data"} 
            ''')
        if file is not None:
            os.system(f'echo {"{}"} > {file}')
        else:
            if os.path.isfile(self.dayChangeJsonFileStringBackupFile):
                os.system(
                    f'cp {self.dayChangeJsonFileStringBackupFile} {self.dayChangeJsonFileString}'
                )
                self.jsonData = json.load(open(self.dayChangeJsonFileString))
            else:
                os.system(
                    f'echo {"{}"} > {self.dayChangeJsonFileStringBackupFile}')
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
        self.summaryTable.add_column('current', justify='right', no_wrap=True)
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
            totalProfitPercentage = self.jsonData['toalProfitPercentage']
            totalProfit = self.jsonData['totalProfit']
        except Exception as e:
            self.console.print(
                'Incomplete info in Json file try [b][yellow]-d y[/yellow][/b] option'
            )
            exit()

        investedString = f'Invested\n\n[bold]₹{invested}[/bold]'
        currentColor = f'[green]₹{current}[/green]' if current >= invested else f'[red]₹{current}[/red]'
        currentString = f'Current\n\n[bold]{currentColor}[/bold]'
        totalReturnString = f'[yellow]•[/yellow]Total Returns\n\n[bold]{getfv(totalProfit)} {getfp(totalProfitPercentage)}[/bold]'
        lastUpdatedString = f'Last Updated\n\n[b][yellow]{lastUpdated}[/yellow][/b]'
        self.summaryTable.add_row(investedString, currentString,
                                  totalReturnString, lastUpdatedString)

    def MutualFundTableEdit(self, id: str) -> None:
        try:
            preMF = self.jsonData[id]
            SchemeName = preMF['name']
            dayChange = preMF['dayChange']
            current = preMF['current']
            invested = preMF['invested']
            date = preMF['latestNavDate']
        except Exception as e:
            self.console.print(
                'Incomplete info in Json file try[yellow][b]-d y[/yellow][/b] option'
            )
            exit()
        if dayChange != 'N.A.':
            dayChangePercentage: float = roundUp3(dayChange / invested * 100)
            dayChangeString = f'{dayChangePercentage}%\n\n[b]{getfv(dayChange)}[/b]'
        else:
            dayChangeString = f'N.A.\n\n[b]N.A.[/b]'

        returns = roundUp3(current - invested)

        returnsPercentage = returns / invested * 100

        returnString = f'₹{returns}\n\n[b]{getfp(returnsPercentage)}[/b]'
        currentString = f'₹{current}\n\n[b]₹{invested}[/b]'
        nav_date = f'[yellow]{date}[/yellow]\n\n[b]{preMF["nav"][date]}[/b]'

        self.TableMutualFund.add_row(SchemeName, dayChangeString, returnString,
                                     currentString, nav_date)

    def dayChangeTableAll(self, dic: dict):
        all_daily_table = Table(title='Day Change Total',
                                show_lines=True,
                                expand=True)
        all_daily_table.add_column('NAV', justify='center', no_wrap=True)
        all_daily_table.add_column('DayChange', justify='center', no_wrap=True)

        nav_col = ''
        dayChange_col = ''
        for nav, dayChange in dic.items():
            nav_col += f'[yellow]{nav}[/yellow]\n'
            dayChange_col += f'{getfv(dayChange)}\n'
        all_daily_table.add_row(nav_col, dayChange_col)
        self.console.print(all_daily_table)
        print(end="\n\n")
        dates: list = list(dic.keys())
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
            value: dict = self.jsonData[key]['nav']
            name = self.jsonData[key]['name']
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

    def writeToJsonFile(self) -> None:
        logging.info("--writing to the dayChange file--")
        with open(self.dayChangeJsonFileString, 'w') as outfile:
            json.dump(self.jsonData, outfile, indent=4)

    def getGrepString(self) -> str:
        unitKeyList = list(self.Units.keys())

        grepSearchString = ''
        for i in range(len(unitKeyList)):
            if i == 0:
                grepSearchString += unitKeyList[i]
            else:
                grepSearchString += '\|' + unitKeyList[i]
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
        if not os.path.isfile(self.navallfile):
            self.downloadAllNavFile()

        var = os.system(f'''
            grep -wi '{self.getGrepString()}' {self.navallfile} > {self.navMyfile}

            ''')
        if var:
            print('something went wrong')
            exit()

    def downloadAllNavFile(self) -> None:
        logging.info("--downloading the NAV file from server--")
        start = time.time()

        var = os.system(f'''
            mv {self.navallfile} {self.navallfile+'.bak'}
            cp {self.dayChangeJsonFileString} {self.dayChangeJsonFileStringBackupFile}
            wget  -q --timeout=20 --tries=10 --retry-connrefused  "https://www.amfiindia.com/spages/NAVopen.txt" -O {self.navallfile}
        ''')
        if var:
            logging.info(
                "something went wrong can\'t download the file Rolling back to previous NAV file"
            )
            os.system(f'''
                mv {self.navallfile+'.bak'} {self.navallfile}
                ''')
        else:
            logging.info(
                f"took {round(time.time()-start,2)} Secs to download the file")
            new_hash = hashlib.md5(open(self.navallfile,
                                        'rb').read()).hexdigest()
            if self.jsonData.__contains__('hash'):
                prev_hash = self.jsonData['hash']
                if prev_hash == new_hash:
                    logging.info("--No changes found in the new NAV file--")
            self.jsonData['hash'] = new_hash
            lastUpdated = datetime.now().strftime(self.formatString + " %X")
            self.jsonData['lastUpdated'] = lastUpdated
            os.system(f"rm -f {self.navallfile+'.bak'}")

    def dayChangeMethod(self, ids: str, todayNav: float, latestNavDate: str,
                        name: str) -> float:

        dayChange = 0.0
        self.isExistingId(ids, name, latestNavDate, todayNav)
        data = self.jsonData[ids]['nav']
        latestDate = datetime.strptime(latestNavDate, self.formatString)

        prevDayNavDate = datetime.strftime(latestDate - timedelta(1),
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
        keys = list(self.jsonData.keys())
        for key in keys:
            if key.isnumeric() and key not in self.Units:
                del self.jsonData[key]

        self.writeToJsonFile()

    def getCurrentValues(self, download: bool) -> None:
        logging.info("--Main calculation--")
        cur_json = self.jsonData
        if download:
            self.addToUnitsNotPreEXisting()
            self.downloadAllNavFile()
        self.updateMyNaVFile()

        sumTotal = 0
        totalInvested = 0
        totalDaychange = 0
        totalProfit = 0
        totalProfitPercentage = 0
        file = open(self.navMyfile)

        for line in file:
            current = 0
            dayChange = 0

            temp = line.strip().split(";")
            id, name, nav, date = temp[0], temp[3].split(
                '-')[0].strip(), float(temp[4]), temp[5]

            dayChange = self.dayChangeMethod(id, nav, date, name)

            current = round(self.Units[id][0] * nav, 3)
            invested = self.Units[id][1]
            sumTotal += current
            totalInvested += invested

            cur_json_id: dict = cur_json[id]
            cur_json_id['latestNavDate'] = date
            cur_json_id['current'] = current
            cur_json_id['invested'] = invested
            cur_json_id['dayChange'] = dayChange

        totalProfit = sumTotal - totalInvested
        totalProfitPercentage = totalProfit / totalInvested * 100

        totalProfitPercentage = round(totalProfitPercentage, 3)
        totalProfit = round(totalProfit, 3)
        totalDaychange = round(totalDaychange, 3)
        cur_json['totalProfit'] = totalProfit
        cur_json['sumTotal'] = round(sumTotal, 3)
        cur_json['totalInvested'] = totalInvested
        cur_json['toalProfitPercentage'] = totalProfitPercentage

        self.writeToJsonFile()
        file.close()


if __name__ == "__main__":
    tracker = MutualFund()
