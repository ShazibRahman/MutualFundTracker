import argparse
from MutualFundTracker import MutualFund


def callMutualFund() -> None:
    tracker = MutualFund()
    if(args.add is not None):
        tracker.addOrder(args.add[0],int(args.add[1]),float(args.add[2]),args.add[3])
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
    parser.add_argument("-dc",
                        type=str, choices=['y', 'n'], default='n')
    parser.add_argument("-add",nargs="+", type=str)
    args = parser.parse_args()
    callMutualFund()
