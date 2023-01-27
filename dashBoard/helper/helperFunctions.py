from datetime import datetime
import json
from typing import Dict, List
import nsepy
import os


data_path = os.path.join(os.path.dirname(__file__)+"/../../")


def roundup3(x):
    return round(x, 3)


def readJsonFile(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def writeJsonFile(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


units_json = readJsonFile(data_path+'data/units.json')
daychange_json = readJsonFile(data_path+'data/dayChange.json')
Orders = readJsonFile(data_path+'data/order.json')


def addOrder(MFID, unit, amount, date) -> None:
    '''
        mfid , unit : float , amount :float , date : for ex 07-May-2022
    '''
    # print("called with id: ", MFID, " and value: ",
    #       daychange_json[MFID]['name'])
    if Orders.__contains__(MFID) and Orders[MFID].__contains__(
            date):
        data = Orders[MFID][date]
        data[0] += unit
        data[1] += amount
    elif Orders.__contains__(MFID):
        Orders[MFID][date] = [unit, amount]
    else:
        Orders[MFID] = {}
        Orders[MFID][date] = [unit, amount]
    writeJsonFile(data_path+'data/order.json', Orders)


mutual_funds_dic = {daychange_json[unit]['name']: unit for unit in units_json}
mutual_funds = list(mutual_funds_dic.keys())


def getDailyChange():
    sumDayChange: dict = {}
    for val in units_json.keys():
        value: dict[str, float] = daychange_json[val]['nav']
        units: float = units_json[val][0]
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
            prevdayChange = daychange
    return [{'x': list(sumDayChange.keys()), 'y': list(sumDayChange.values()), 'type': 'line', 'name': 'Daily Change'}]


def dailyChangePerMutualFund(id):
    # print("called with id: ", id, " and value: ", daychange_json[id]['name'])
    sumDayChange: dict = {}
    units: float = units_json[id][0]
    value = daychange_json[id]['nav']
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
        prevdayChange = daychange
    return [{'x': list(sumDayChange.keys()), 'y': list(
        sumDayChange.values()), 'type': 'line', 'name': daychange_json[id]['name']+" Daily Change"}], daychange_json[id]['name']


def return_data(value):
    return_list = []

    data = daychange_json[value]['nav']
    x = list(data.keys())
    y = list(data.values())
    return_list.append({'x': x, 'y': y, 'type': 'line',
                        'name': daychange_json[value]['name']})

    return return_list, daychange_json[value]['name']


def get_options():
    return [{"label": x, "value": mutual_funds_dic[x]} for x in mutual_funds]


def get_id_name_dic():
    return {unit: daychange_json[unit]['name'] for unit in units_json}


def getInvestmentDistribution():
    data_at_time_of_investment = {}
    data_current = {}
    for val in units_json.keys():
        mutual_fund = daychange_json[val]
        data_current[mutual_fund['name']
                     ] = mutual_fund['current']
        data_at_time_of_investment[mutual_fund['name']
                                   ] = mutual_fund['invested']
    return data_at_time_of_investment, data_current


def getMainTableData():
    summaryTable = [['Invested', 'Current', '•Total Returns', 'Last UpDated']]
    lastUpdated = daychange_json['lastUpdated']
    current = daychange_json['sumTotal']
    invested = daychange_json['totalInvested']
    totalProfitPercentage = daychange_json['totalProfitPercentage']
    totalProfit = daychange_json['totalProfit']
    summaryTable.append([invested, current, str(totalProfit) +
                        " "+str(totalProfitPercentage), lastUpdated])
    mutual_fund_table: List[List] = [
        "SCHEME NAME,DAY CHANGE,RETURNS,CURRENT,NAV".split(",")]

    for val in units_json.keys():
        daychngeString = ""
        preMF = daychange_json[val]
        SchemeName = preMF['name']
        dayChange = preMF['dayChange']
        current = preMF['current']
        invested = preMF['invested']
        date = preMF['latestNavDate']
        if dayChange != 'N/A':
            dayChangePercentage = roundup3(dayChange/invested*100)
            daychngeString = f"{dayChangePercentage}% {dayChange}"
        else:
            daychngeString = "N/A|N/A"
        returns = roundup3(current-invested)
        returnsPercentage = roundup3(returns/invested*100)
        returnsString = f"{returns} {returnsPercentage}%"
        currentString = f"{current} {invested}"
        nav_date = f'{date} {preMF["nav"][date]}'
        mutual_fund_table.append(
            [SchemeName, daychngeString, returnsString, currentString, nav_date])

    return summaryTable, mutual_fund_table


def get_history(symbol: str, start: str, end: str) -> Dict:
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')
    return nsepy.get_history(symbol, start=start_date, end=end_date)
