import argparse
from MutualFundTracker import MutualFund


def callMutualFund():
    tracker = MutualFund()
    if args.g == 'y' and args.d == 'y':
        tracker.download = True
        tracker.getCurrentValues()
        tracker.writeToJsonFile()
        tracker.drawGraph()
    elif args.d == 'y' and args.g == 'n':
        tracker.download = True
        tracker.getCurrentValues()

        tracker.writeToJsonFile()

    elif args.g == 'y' and args.d == 'n':
        tracker.drawGraph()

    else:
        tracker.download = False
        tracker.getCurrentValues()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d',
                        type=str,
                        default='n',
                        help='set whether to download new files')
    parser.add_argument('-g',
                        type=str,
                        default='n',
                        help='draw a graph')
    args = parser.parse_args()
    callMutualFund()
