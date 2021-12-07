import argparse
from MutualFundTracker import MutualFund


def callMutualFund():
    tracker = MutualFund()
    if args.r == 'y':
        tracker.getCurrentValues(False)
        tracker.drawTable()
        return
    if args.d == 'y':
        tracker.getCurrentValues(True)
    if args.g != 'o':
        tracker.drawTable()
    if args.g == 'y' or args.g == 'o':
        tracker.drawGraph()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        type=str,
                        default='n',
                        help='set whether to download new files',
                        choices=['y', 'n']
                        )
    parser.add_argument('-g',
                        type=str,
                        default='n',
                        help='draw a graph',
                        choices=['y', 'n', 'o']
                        )
    parser.add_argument("-t",
                        type=str,
                        default='y',
                        help='Render the tables',
                        choices=['y', 'n']
                        )
    parser.add_argument("-r",
                        type=str,
                        default='n',
                        choices=['y', 'n'])
    args = parser.parse_args()
    callMutualFund()
