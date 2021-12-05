import json
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
import os
import time
import plotext as plt


def getfv(number: float) -> str:
    return f'[green]+₹{number}[/green]' if number >= 0 else f'[red]-₹{-(number)}[/red]'


def getfp(number: float) -> str:
    return f'[green]({number}%)[/green]' if number >= 0 else f'[red]({number})%[/red]'


class MutualFund:
    def __init__(self) -> None:
        self.Units = {
            # icici shortTerm
            '120754': [89.058, 4500],
        }
        self.TableMutualFund = None
        self.summaryTable = None

        self.initializeTables()
        self.unitsKeyList = list(self.Units.keys())
        self.directoryString = os.path.dirname(__file__)
        self.navallfile = self.directoryString + "/data/" + "NAVAll.txt"
        self.navMyfile = self.directoryString + "/data/" + "nav.txt"
        self.dayChangeJsonFileString = self.directoryString + "/data/dayChange.json"
        try:
            self.jsonData = json.load(open(self.dayChangeJsonFileString))
        except:
            self.jsonData = {}  # initialize to an empty dic inCase the JsonFile Doesn't exist
        self.formatString = "%d-%b-%Y"
        self.responseTime = 0

    def initializeTables(self) -> None:
        self.TableMutualFund = Table(
            expand=True)

        self.summaryTable = Table.grid(expand=True)

        self.summaryTable.add_column(
            'invested', justify='center', no_wrap=True)
        self.summaryTable.add_column('current', justify='right', no_wrap=True)
        self.summaryTable.add_column(
            'total returns', justify='right', no_wrap=True)
        self.summaryTable.add_column(
            'lastUpdated and NAV date', justify='center', no_wrap=True)

        self.TableMutualFund.add_column(
            'SCHEME NAME', justify='center')
        self.TableMutualFund.add_column(
            'DAY CHANGE', justify='center')
        self.TableMutualFund.add_column(
            'RETURNS', justify='center')
        self.TableMutualFund.add_column(
            'CURRENT', justify='center')

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
        totalReturnString = f'Total Returns\n\n[bold]{getfv(totalProfit)} {getfp(totalProfitPercentage)}[/bold]'
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
        except Exception as e:
            self.console.print(
                'Incomplete info in Json file try[yellow][b]-d y[/yellow][/b] option')
            exit()
        dayChangePercentage = round(dayChange / invested * 100, 3)
        returns = round(current - invested, 3)

        returnsPercentage = round(returns / invested * 100, 3)

        dayChangeString = f'{dayChangePercentage}%\n\n{getfv(dayChange)}'
        returnString = f'₹{returns}\n\n{getfp(returnsPercentage)}'
        currentString = f'₹{current}\n\n₹{invested}'

        self.TableMutualFund.add_row(
            SchemeName, dayChangeString, returnString, currentString)

    def drawTable(self):
        console = Console()
        self.summaryTableEdit()
        print(end="\n\n")
        console.print(self.summaryTable)
        for ids in self.unitsKeyList:
            self.MutualFundTableEdit(ids)
        console.print(self.TableMutualFund)
        print(end="\n\n")

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
                          label='profit plot')
            # plt.plot([0])
            plt.show()
        print()

    def OsrealatedStuff(self, greString: str) -> None:

        var = os.system(
            f'''
            wget  -q   "https://www.amfiindia.com/spages/NAVopen.txt" -O {self.navallfile}
        '''
        )
        if var:
            print('something went wrong can\'t download the file')
        os.system(
            f'''
            grep -wi '{greString}' {self.navallfile} > {self.navMyfile}

            '''
        )

    def dayChangeMethod(self, ids: str, todayProfit: float, latestNavDate: str, name: str) -> float:

        dayChange = 0.0
        self.isExistingId(ids, name, latestNavDate, todayProfit)
        data = self.jsonData[ids]['nav']
        latestDate = datetime.strptime(
            latestNavDate, self.formatString)

        prevDayNavDate = datetime.strftime(
            latestDate - timedelta(1), self.formatString)
        if prevDayNavDate not in data:  # only if nav object is empty or contains latestNavDate only
            data[latestNavDate] = todayProfit
            return dayChange

        prevDayProfit = data[prevDayNavDate]
        dayChange = round(todayProfit - prevDayProfit, 3)
        self.jsonData[ids]['dayChange'] = dayChange
        data[latestNavDate] = todayProfit
        return dayChange

    def isExistingId(self, ids: str, name: str, latestNavDate: str, todayProfit: float) -> None:
        if not self.jsonData.__contains__(ids):
            self.jsonData[ids] = {}
            self.jsonData[ids]['name'] = name
            self.jsonData[ids]['nav'] = {}
            self.jsonData[ids]['nav'][latestNavDate] = todayProfit

    def cleanUp(self) -> None:
        keys = list(self.jsonData.keys())
        for key in keys:
            if key not in self.Units:
                del self.jsonData[key]

    def getCurrentValues(self) -> None:
        cur_json = self.jsonData
        self.OsrealatedStuff(self.getGrepString())
        lastUpdated = datetime.now().strftime(self.formatString + " %X")

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
            todayProfit = round(current-invested, 3)
            sumTotal += current
            totalInvested += invested

            dayChange = self.dayChangeMethod(
                id, todayProfit, date, name)
            totalDaychange += dayChange

            cur_json_id = cur_json[id]
            cur_json_id['name'] = name
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
        self.jsonData['lastUpdated'] = lastUpdated
        self.drawTable()
        self.writeToJsonFile()
        file.close()


if __name__ == "__main__":
    start = time.time()
    tracker = MutualFund()
    tracker.download = True
    tracker.getCurrentValues()
    tracker.writeToJsonFile()
    # tracker.drawGraph()
