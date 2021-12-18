import json
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
import os
import plotext as plt


def getfv(number: float) -> str:
    return f'[green]+₹{number}[/green]' if number >= 0 else f'[red]-₹{abs(number)}[/red]'


def getfp(percentage: float) -> str:
    return f'[green]({percentage}%)[/green]' if percentage >= 0 else f'[red]({percentage})%[/red]'


class MutualFund:
    def __init__(self) -> None:
        self.Units = {
        }
        if not self.Units:
            print('No mutual Fund specified to track')
            exit()

        self.unitsKeyList = list(self.Units.keys())
        self.console = None
        self.TableMutualFund = None
        self.summaryTable = None

        self.directoryString = os.path.dirname(__file__)
        self.navallfile = self.directoryString + "/data/NAVAll.txt"
        self.navMyfile = self.directoryString + "/data/nav.txt"
        self.dayChangeJsonFileString = self.directoryString + "/data/dayChange.json"
        try:
            self.jsonData = json.load(open(self.dayChangeJsonFileString))
        except:
            # initialize to an empty dic inCase the JsonFile Doesn't exist or have invalid data
            self.jsonData = {}
        self.formatString = "%d-%b-%Y"

    def initializeTables(self) -> None:
        if len(self.unitsKeyList) == 0:
            print('no Mutual Fund found')
            exit()
        self.TableMutualFund = Table(
            expand=True, show_lines=True,)
        self.summaryTable = Table.grid(expand=True, pad_edge=True, padding=2)

        self.summaryTable.add_column(
            'invested', justify='center', no_wrap=True)
        self.summaryTable.add_column('current', justify='right', no_wrap=True)
        self.summaryTable.add_column(
            'total returns', justify='right', no_wrap=True)
        self.summaryTable.add_column(
            'lastUpdated', justify='right', no_wrap=True)

        self.TableMutualFund.add_column(
            'SCHEME NAME', justify='center')
        self.TableMutualFund.add_column(
            'DAY CHANGE', justify='center')
        self.TableMutualFund.add_column(
            'RETURNS', justify='center')
        self.TableMutualFund.add_column(
            'CURRENT', justify='center')
        self.TableMutualFund.add_column(
            'NAV', justify='center')

    def summaryTableEdit(self) -> None:
        try:
            lastUpdated = self.jsonData['lastUpdated']
            current = self.jsonData['sumTotal']
            invested = self.jsonData['totalInvested']
            totalProfitPercentage = self.jsonData['toalProfitPercentage']
            totalProfit = self.jsonData['totalProfit']
        except Exception as e:
            self.console.print(
                'Incomplete info in Json file try [b][yellow]-d y[/yellow][/b] option')
            exit()

        investedString = f'Invested\n\n[bold]₹{invested}[/bold]'
        currentColor = f'[green]₹{current}[/green]' if current >= invested else f'[red]₹{current}[/red]'
        currentString = f'Current\n\n[bold]{currentColor}[/bold]'
        totalReturnString = f'[yellow]•[/yellow]Total Returns\n\n[bold]{getfv(totalProfit)} {getfp(totalProfitPercentage)}[/bold]'
        lastUpdatedString = f'Last Updated\n\n[b][yellow]{lastUpdated}[/yellow][/b]'
        self.summaryTable.add_row(
            investedString, currentString, totalReturnString, lastUpdatedString)

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
                'Incomplete info in Json file try[yellow][b]-d y[/yellow][/b] option')
            exit()
        if dayChange != 'N.A.':
            dayChangePercentage = round(dayChange / invested * 100, 3)
            dayChangeString = f'{dayChangePercentage}%\n\n[b]{getfv(dayChange)}[/b]'
        else:
            dayChangeString = f'N.A.\n\n[b]N.A.[/b]'

        returns = round(current - invested, 3)

        returnsPercentage = round(returns / invested * 100, 3)

        returnString = f'₹{returns}\n\n[b]{getfp(returnsPercentage)}[/b]'
        currentString = f'₹{current}\n\n[b]₹{invested}[/b]'
        nav_date = f'[b][yellow]{date}[/yellow][/b]'

        self.TableMutualFund.add_row(
            SchemeName, dayChangeString, returnString, currentString, nav_date)

    def DayChangeTable(self):
        daily_table = Table(title='Day Change table',
                            show_lines=True, expand=True)
        daily_table.add_column('SCHEME NAME', justify='center', no_wrap=True)
        daily_table.add_column('NAV', justify='center', no_wrap=True)
        daily_table.add_column('DayChange', justify='center', no_wrap=True)

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
                    prevdayChange = units*daychange
                    i = False
                    continue
                nav_col += f'[yellow]{nav}[/yellow]\n'
                daychangeData = daychange*units
                daychange_col += f'{getfv(round(daychangeData-prevdayChange,3))}\n'
                prevdayChange = daychangeData

            daily_table.add_row(name, nav_col, daychange_col)
        if not self.console:
            self.console = Console()
        print("\n")
        self.console.print(daily_table)
        print("\n")

    def drawTable(self):
        self.initializeTables()
        self.console = Console()
        self.summaryTableEdit()
        self.console.print(self.summaryTable)
        for ids in self.unitsKeyList:
            self.MutualFundTableEdit(ids)
        self.console.print(self.TableMutualFund)

    def writeToJsonFile(self) -> None:
        with open(self.dayChangeJsonFileString, 'w') as outfile:
            json.dump(self.jsonData, outfile, indent=4)

    def getGrepString(self) -> str:

        grepSearchString = ''
        for i in range(len(self.unitsKeyList)):
            if i == 0:
                grepSearchString += self.unitsKeyList[i]
            else:
                grepSearchString += '\|' + self.unitsKeyList[i]
        return grepSearchString

    def drawGraph(self) -> None:
        plt.datetime.set_datetime_form(date_form=self.formatString)
        for ids in self.unitsKeyList:
            value = self.jsonData[ids]
            print()
            x = value['nav'].keys()
            y = value['nav'].values()
            plt.plot_size(100, 30)
            plt.title(value['name'])
            plt.xlabel('Date', xside='upper')
            plt.ylabel('profit', yside='left')

            plt.plot_date(x, y, color='green',
                          label='Nav Plot')
            # plt.plot([0])
            plt.show()
        print()

    def updateMyNaVFile(self):

        os.system(
            f'''
            grep -wi '{self.getGrepString()}' {self.navallfile} > {self.navMyfile}

            '''
        )

    def downloadAllNavFile(self) -> None:

        var = os.system(
            f'''
            mv {self.navallfile} {self.navallfile+'.bak'}
            wget  -q --timeout=1 --tries=5 --retry-connrefused  "https://www.amfiindia.com/spages/NAVopen.txt" -O {self.navallfile}
        '''
        )
        if var:
            print('something went wrong can\'t download the file')
            os.system(
                f'''
                mv {self.navallfile+'.bak'} {self.navallfile}
                '''
            )
        else:
            lastUpdated = datetime.now().strftime(self.formatString + " %X")
            self.jsonData['lastUpdated'] = lastUpdated
            os.system(
                f"rm -f {self.navallfile+'.bak'}"
            )

    def dayChangeMethod(self, ids: str, todayNav: float, latestNavDate: str, name: str) -> float:

        dayChange = 0.0
        self.isExistingId(ids, name, latestNavDate, todayNav)
        data = self.jsonData[ids]['nav']
        latestDate = datetime.strptime(
            latestNavDate, self.formatString)

        prevDayNavDate = datetime.strftime(
            latestDate - timedelta(1), self.formatString)

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
        units: float = self.Units[ids][0]

        prevDaySum: float = data[prevDayNavDate]*units
        dayChange: float = round(todayNav*units - prevDaySum, 3)
        self.jsonData[ids]['dayChange'] = dayChange
        data[latestNavDate] = todayNav
        return dayChange

    def isExistingId(self, ids: str, name: str, latestNavDate: str, todayNav: float) -> None:
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
        cur_json = self.jsonData
        if download:
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

            current = round(self.Units[id][0] * nav, 3)
            invested = self.Units[id][1]
            sumTotal += current
            totalInvested += invested

            dayChange = self.dayChangeMethod(
                id, nav, date, name)

            totalDaychange += dayChange if dayChange != 'N.A.' else 0.00

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
        cur_json['totalDayChange'] = totalDaychange

        self.writeToJsonFile()
        file.close()


if __name__ == "__main__":
    tracker = MutualFund()
    tracker.DayChangeTable()
