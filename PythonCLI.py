import argparse
from MutualFundTracker import MutualFund
import os

loggerPath = os.path.dirname(__file__) + "/data/logger.log"


def readLogs():
    # file = open(loggerPath, 'r')
    # print(file.read(), end='')
    os.system(f'bat --line-range 50: --paging=never {loggerPath}')
    return


def clearLogs():
    file = open(loggerPath, 'w')
    file.close()
    return


def callMutualFund() -> None:
    if (args.logs == "show"):
        readLogs()
        return
    if (args.logs == "clear"):
        clearLogs()
        return
    tracker = MutualFund()
    if (args.add is not None):
        tracker.addOrder(args.add[0], float(args.add[1]), float(args.add[2]),
                         args.add[3])
        return
    if args.dc == 'y':
        tracker.DayChangeTable()
        return

    if args.r == 'y':
        tracker.getCurrentValues(False)

    if args.d == 'y':
        tracker.getCurrentValues(True)
    if args.g != 'o':
        tracker.drawTable()
    if args.g == 'y' or args.g == 'o':
        tracker.drawGraph()
        return


if __name__ == '__main__':
    choices = ['y', 'n']
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        type=str,
                        default='n',
                        help='set whether to download new files',
                        choices=choices)
    parser.add_argument('-g',
                        type=str,
                        default='n',
                        help='draw a graph',
                        choices=['y', 'n', 'o'])
    parser.add_argument("-t",
                        type=str,
                        default='y',
                        help='Render the tables',
                        choices=choices)
    parser.add_argument("-r", type=str, default='n', choices=['y', 'n'])
    parser.add_argument("-dc", type=str, choices=choices, default='n')
    parser.add_argument("-add",
                        nargs="+",
                        type=str,
                        help="Mf unit amount date [dd-mon-yyyy]")
    parser.add_argument("--logs",
                        type=str,
                        choices=['show', 'clear', 'n'],
                        default='n')
    parser.add_argument("-logs",
                        type=str,
                        choices=['show', 'clear', 'n'],
                        default='n')
    args = parser.parse_args()
    callMutualFund()
