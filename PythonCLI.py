import argparse
import os
try:
    from git import Repo
except ImportError:
    if os.name == 'nt':
        os.system('pip install gitpython')
    else:
        os.system('pip3 install gitpython')
    from git import Repo
git_dir = os.path.dirname(__file__)
loggerPath = os.path.dirname(__file__) + "/data/logger.log"
anacron_user = "Shazib_Anacron"


def readLogs():
    os.system(f'bat --paging=never {loggerPath}')
    return


def clearLogs():
    file = open(loggerPath, 'w')
    file.close()
    return


def callMutualFund() -> None:
    if args.logs == "show":
        readLogs()
        return

    if args.logs == "clear":
        clearLogs()
        return

    if args.add is not None:

        from MutualFundTracker import MutualFund
        tracker = MutualFund()
        tracker.addOrder(args.add[0], float(args.add[1]), float(args.add[2]),
                         args.add[3])
        return
    if args.dc == 'y':

        from MutualFundTracker import MutualFund
        tracker = MutualFund()
        tracker.DayChangeTable()
        return

    if args.r == 'y':
        from MutualFundTracker import MutualFund
        tracker = MutualFund()
        tracker.getCurrentValues(False)
        tracker.drawTable()
        return

    if args.d == 'y':

        from MutualFundTracker import MutualFund
        tracker = MutualFund()
        repo = Repo(git_dir)
        try:
            tracker.logging.info("Pulling the latest changes")
            repo.remotes.origin.pull()
            tracker.logging.info("Pulling successful")
        except:
            tracker.logging.info("Pulling failed")
            return

        from MutualFundTracker import MutualFund
        tracker = MutualFund()
        tracker.getCurrentValues(True)
        tracker.drawTable()

        try:
            tracker.logging.info("Pushing the latest changes")
            repo.remotes.origin.push()
            tracker.logging.info("Pushing successful")
        except Exception as e:
            tracker.logging.info("Pushing failed")
            tracker.logging.info(e)
            return

        return

    if args.g != 'o':
        from MutualFundTracker import MutualFund
        tracker = MutualFund()
        tracker.drawTable()

    if args.g == 'y' or args.g == 'o':
        from MutualFundTracker import MutualFund
        tracker = MutualFund()
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
    parser.add_argument("-r", type=str,
                        default='n',
                        choices=['y', 'n'])
    parser.add_argument("-dc", type=str,
                        choices=choices,
                        default='n')
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
else:
    raise RuntimeError("this script is not meant to be imported")
