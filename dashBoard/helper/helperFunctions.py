import json
import pathlib
import sys
from datetime import datetime
from typing import List

import nsepy
import requests
from pandas import DataFrame

sys.path.append(pathlib.Path(
    __file__).parent.parent.parent.absolute().as_posix())

from gdrive.GDrive import GDrive  # autopep8: off

data_path = pathlib.Path(__file__).parent.parent.parent.joinpath(
    "data").resolve().as_posix()


gdrive: GDrive = GDrive()


def roundup3(x):
    return round(x, 3)


def readJsonFile(filename):
    gdrive.download(filename)
    with open(filename, 'r') as f:
        return json.load(f)


def readJsonFromDataFolder(filename):
    file_path = pathlib.Path(data_path).joinpath(filename).resolve()
    gdrive.download(file_path)
    with open(file_path, 'r') as f:
        return json.load(f)


def writeJsonFile(filename, data):
    print("writing to file : ", filename)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    gdrive.upload(filename)

unit_file_path = pathlib.Path(data_path).joinpath("units.json").resolve()
daychange_file_path = pathlib.Path(data_path).joinpath("dayChange.json").resolve()
order_file_path = pathlib.Path(data_path).joinpath("order.json").resolve()
json_data_file_path = pathlib.Path(data_path).joinpath("NAVAll.json").resolve()
stock_data_file_path = pathlib.Path(data_path).joinpath("stocks_data.json").resolve()
stock_order_file_path = pathlib.Path(data_path).joinpath("stock_order.json").resolve()

units_json = readJsonFile(unit_file_path)
daychange_json = readJsonFile(daychange_file_path)
Orders = readJsonFile(order_file_path)
json_data = readJsonFile(json_data_file_path)



def add_order_stock(stock, units, amount):
    stock_order = readJsonFile(stock_order_file_path)
    stock_data = readJsonFile(stock_data_file_path)
    if not stock_data.__contains__(stock):
        return False
    if stock_order.__contains__(stock):
        stock_order[stock][0] += units
        stock_order[stock][1] += amount*units
    else:
        stock_order[stock] = [units, amount*units]
    writeJsonFile(stock_order_file_path, stock_order)
    return True


def addOrder(MFID, unit, amount, date) -> str:
    """
        mfid , unit : float , amount :float , date : for ex 07-May-2022
    """
    value = "old"
    if Orders.__contains__(MFID) and Orders[MFID].__contains__(date):
        data = Orders[MFID][date]
        data[0] += unit
        data[1] += amount
    elif Orders.__contains__(MFID):
        Orders[MFID][date] = [unit, amount]
    else:
        Orders[MFID] = {}
        Orders[MFID][date] = [unit, amount]
        value = "new"
    writeJsonFile(order_file_path, Orders)
    return value


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
    sum_daychange_sorted_keys = sorted(
        sumDayChange.keys(), key=lambda x: datetime.strptime(x, '%d-%b-%Y'))
    # sorted by key, return a dict
    sumDayChange = {k: sumDayChange[k] for k in sum_daychange_sorted_keys}
    return [{'x': list(sumDayChange.keys()), 'y': list(sumDayChange.values()), 'type': 'line', 'name': 'Daily Change'}]


def dailyChangePerMutualFund(id_):
    # print("called with id: ", id, " and value: ", daychange_json[id]['name'])
    sumDayChange: dict = {}
    units: float = units_json[id_][0]
    value = daychange_json[id_]['nav']
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
        sumDayChange.values()),
        'type': 'line', 'name': daychange_json[id_]['name'] + " Daily Change"}], \
        daychange_json[id_]['name']


def return_data(value):
    return_list = []

    data = daychange_json[value]['nav']
    x = list(data.keys())
    y = list(data.values())
    return_list.append({'x': x, 'y': y, 'type': 'line',
                        'name': daychange_json[value]['name']})

    return return_list, daychange_json[value]['name']


def get_options():
    # print(mutual_funds_dic)
    return [{"label": x, "value": mutual_funds_dic[x]} for x in mutual_funds]


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

        preMF = daychange_json[val]
        SchemeName = preMF['name']
        dayChange = preMF['dayChange']
        current = preMF['current']
        invested = preMF['invested']
        date = preMF['latestNavDate']
        if dayChange != 'N.A.':
            # print(dayChange)
            dayChangePercentage = roundup3(dayChange/invested*100)
            daychange_string = f"{dayChangePercentage}% {dayChange}"
        else:
            daychange_string = "N.A. N.A."
        returns = roundup3(current-invested)
        returnsPercentage = roundup3(returns/invested*100)
        returnsString = f"{returns} {returnsPercentage}%"
        currentString = f"{current} {invested}"
        nav_date = f'{date} {preMF["nav"][date]}'
        mutual_fund_table.append(
            [SchemeName, daychange_string, returnsString, currentString, nav_date])

    return summaryTable, mutual_fund_table


def get_history(symbol: str, start: str, end: str) -> DataFrame:
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')
    return nsepy.get_history(symbol, start=start_date, end=end_date)


def create_index_all_mutual_fund():
    index_all_mutual_fund = {}
    with requests.get("https://www.amfiindia.com/spages/NAVopen.txt") as response:
        for line in response.text.splitlines():
            if line=="": continue
            if line[0].isdigit():
                data = line.split(";")
                index_all_mutual_fund[data[3]] = data[0]
    writeJsonFile(json_data_file_path,index_all_mutual_fund)


def get_index_all_mutual_fund():
    return [{"label": x, "value": json_data[x]} for x in json_data]


def get_id_name_dic(value):
    value = str(value)
    key = [k for k, v in json_data.items() if value == v]
    return key[0]


def get_all_stocks_list():
    stock_data = readJsonFile(stock_data_file_path)
    return [{"label": stock_data[x], "value":x} for x in stock_data]


def get_all_stock_dic():
    return readJsonFile(stock_data_file_path)


if __name__ == "__main__":
    create_index_all_mutual_fund()
