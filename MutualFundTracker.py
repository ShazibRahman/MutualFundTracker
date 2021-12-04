import json
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
import os
import time
import plotext as plt


class MutualFund:
    def __init__(self) -> None:
        self.Units = {
            # icici shortTerm


        }
        self.unitsKeyList = list(self.Units.keys())

        self.console = Console()
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

        self.download = False

        self.directoryString = os.path.dirname(__file__)
        self.navallfile = self.directoryString+"/data/"+"NAVAll.txt"
        self.navMyfile = self.directoryString+"/data/"+"nav.txt"
        self.dayChangeJsonFileString = self.directoryString+"/data/dayChange.json"
        try:
            self.jsonData = json.load(open(self.dayChangeJsonFileString))
        except:
            self.jsonData = {}  # initialize to an empty dic inCase the JsonFile Doesn't exist
        self.whetherToWrite = False
        self.grepString = self.getGrepString()
        self.formatString = "%d-%b-%Y"
        self.responseTime = 0

    def getfv(self, number):
        return f'[green]+₹{number}[/green]' if number >= 0 else f'[red]-₹{-(number)}[/red]'

    def getfp(self, number):
        return f'[green]({number}%)[/green]' if number >= 0 else f'[red]({number})%[/red]'

    def summaryTableEdit(self, latestNavDate):
        lastUpdated = self.jsonData['lastUpdated']
        current = self.jsonData['sumTotal']
        invested = self.jsonData['totalInvested']
        totalProfitPercentage = self.jsonData['toalProfitPercentage']
        totalProfit = self.jsonData['totalProfit']

        investedString = f'Invested\n\n[bold]₹{invested}[/bold]'
        currentColor = f'[green]₹{current}[/green]' if current >= invested else f'[red]₹{current}[/red]'
        currentString = f'Current\n\n[bold]{currentColor}[/bold]'
        totalReturnString = f'Total Returns\n\n[bold]{self.getfv(totalProfit)} {self.getfp(totalProfitPercentage)}[/bold]'
        lastUpdatedString = f'NAV Date\t{latestNavDate}\n\nLast Updated {lastUpdated}'
        self.summaryTable.add_row(
            investedString, currentString, totalReturnString, lastUpdatedString)

    def MutualFundTableEdit(self, id: str):
        preMF = self.jsonData[id]
        SchemeName = preMF['name']
        dayChange = preMF['dayChange']
        current = preMF['current']
        invested = preMF['invested']

        dayChangePercentage = round(dayChange/invested*100, 3)
        returns = round(current-invested, 3)

        returnsPercentage = round(returns/invested*100, 3)

        dayChangeString = f'{dayChangePercentage}%\n\n{self.getfv(dayChange)}'
        returnString = f'₹{returns}\n\n{self.getfp(returnsPercentage)}'
        currentString = f'₹{current}\n\n₹{invested}'

        self.TableMutualFund.add_row(
            SchemeName, dayChangeString, returnString, currentString)

    def writeToJsonFile(self) -> None:

        if (self.whetherToWrite):
            with open(self.dayChangeJsonFileString, 'w') as outfile:
                json.dump(self.jsonData, outfile, indent=4)

    def getGrepString(self):

        grepSearchString = ''
        for i in range(len(self.unitsKeyList)):
            if i == 0:
                grepSearchString += self.unitsKeyList[i]
            else:
                grepSearchString += '\|'+self.unitsKeyList[i]
        return grepSearchString

    def drawGraph(self):
        plt.datetime.set_datetime_form(date_form=self.formatString)
        for id, value in self.jsonData.items():
            if id.isnumeric():
                print()
                x = value['nav'].keys()
                y = value['nav'].values()
                plt.plot_size(100, 30)
                plt.title(value['name'])
                plt.xlabel('Date', xside='upper')
                plt.ylabel('profit', yside='left')
                plt.grid(1, 1)

                plt.plot_date(x, y, color='green',
                              label='profit plot')
                # plt.plot([0])
                plt.show()
        print()

    def OsrealatedStuff(self, greString: str) -> None:
        start = time.time()
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
        self.responseTime = time.time() - start

    def dayChangeMethod(self, id: str, todayProfit: int, latestNavDate: str) -> float:

        dayChange = 0.0

        todayProfit = round(todayProfit, 3)
        if not self.jsonData.__contains__(id):
            self.jsonData[id] = {}
            self.jsonData[id]['nav'] = {}
            self.jsonData[id]['nav'][latestNavDate] = todayProfit
            self.whetherToWrite = True
            # print('No previous date found to calculate for above Mutual fund')

        else:

            try:
                data = self.jsonData[id]['nav']
                self.whetherToWrite = True
                latestDate = datetime.strptime(
                    latestNavDate, self.formatString)

                prevDayNavDate = datetime.strftime(
                    latestDate - timedelta(1), self.formatString)
                if prevDayNavDate not in data:
                    keys_list = list(data)
                    prevDayNavDate = keys_list[-1]

                prevDayProfit = data[prevDayNavDate]
                dayChange = round(todayProfit - prevDayProfit, 3)
                self.jsonData[id]['dayChange'] = dayChange
                data[latestNavDate] = todayProfit

            except Exception as e:
                # print('No previous date found to calculate for above Mutual fund')
                pass

        return dayChange

    def cleanUp(self):
        keys = list(self.jsonData.keys())
        for key in keys:
            if key not in self.Units:
                del self.jsonData[key]
        self.whetherToWrite = True

    def getCurrentValues(self):
        cur_json = self.jsonData
        latestDate = None

        if self.download:
            self.OsrealatedStuff(self.grepString)
            lastUpdated = datetime.now().strftime(self.formatString+" %X")
            self.jsonData['lastUpdated'] = lastUpdated
            self.whetherToWrite = True

        change = False
        file = open(self.navMyfile)
        sumTotal = 0
        totalInvested = 0
        totalDaychange = 0
        totalProfit = 0
        totalProfitPercentage = 0
        for line in file:
            current = 0
            dayChange = 0

            temp = line.strip().split(";")
            id, name, nav, date = temp[0], temp[3].split(
                '-')[0].strip(), float(temp[4]), temp[5]
            latestDate = date

            cur_json_id = self.jsonData[id]

            if 'name' not in cur_json_id:
                cur_json_id['name'] = name
                self.whetherToWrite = True
            if date in cur_json_id['nav']:
                current = cur_json_id['current']
                invested = cur_json_id['invested']
                dayChange = cur_json_id['dayChange']

            else:
                current = round(self.Units[id][0]*nav, 3)
                invested = self.Units[id][1]
                cur_json_id['current'] = current
                cur_json_id['invested'] = invested
                sumTotal += current
                totalInvested += invested
                dayChange = self.dayChangeMethod(
                    id, current-invested, date)
                totalDaychange += dayChange
                change = True

            self.MutualFundTableEdit(id)

        if not change:
            totalProfit = cur_json['totalProfit']
            sumTotal = cur_json['sumTotal']
            totalInvested = cur_json['totalInvested']
            totalProfitPercentage = cur_json['toalProfitPercentage']
            totalDaychange = cur_json['totalDayChange']
        else:
            totalProfit = sumTotal - totalInvested
            totalProfitPercentage = totalProfit/totalInvested*100

            totalProfitPercentage = round(totalProfitPercentage, 3)
            totalProfit = round(totalProfit, 3)
            totalDaychange = round(totalDaychange, 3)
            cur_json['totalProfit'] = totalProfit
            cur_json['sumTotal'] = round(sumTotal, 3)
            cur_json['totalInvested'] = totalInvested
            cur_json['toalProfitPercentage'] = totalProfitPercentage
            cur_json['totalDayChange'] = totalDaychange

            self.whetherToWrite = True
        self.summaryTableEdit(latestDate)
        print(end="\n\n")
        self.console.print(self.summaryTable)

        self.console.print(self.TableMutualFund)
        print("\n\n")

        file.close()


if __name__ == "__main__":
    start = time .time()
    tracker = MutualFund()
    tracker.getCurrentValues()
    tracker.writeToJsonFile()
    # tracker.drawGraph()
