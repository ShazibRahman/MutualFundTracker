import argparse
import asyncio
import os

from MutualFundTracker import MutualFund

git_dir = os.path.dirname(__file__)
loggerPath = os.path.dirname(__file__) + "/data/logger.log"
anacron_user = "Shazib_Anacron"
# sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())


def readLogs():
    os.system(f"bat --paging=never {loggerPath}")


def clearLogs():
    file_ = open(loggerPath, "w")
    file_.close()


async def callMutualFund(args) -> None:
    if args.logs == "show":
        readLogs()
        return

    if args.logs == "clear":
        clearLogs()
        return
    if args.dash == "y":
        import webbrowser

        from dashBoard.index import app

        port = 8050

        webbrowser.open(f"http://localhost:{port}")
        app.run_server(debug=True, port=port)  # type: ignore
        return

    if args.add is not None:
        tracker = MutualFund()

        tracker.addOrder(
            args.add[0], float(args.add[1]), float(args.add[2]), args.add[3]
        )
        return
    if args.dc == "y":
        tracker = MutualFund()
        await tracker._intialiaze()

        await tracker.DayChangeTable()
        return

    if args.r == "y":
        tracker = MutualFund()
        await tracker._intialiaze()
        await tracker.getCurrentValues(False)
        tracker.drawTable()
        return

    if args.d == "y":
        tracker = MutualFund()
        await tracker._intialiaze()

        await tracker.getCurrentValues(True)
        tracker.drawTable()

        return

    if args.g != "o":
        tracker = MutualFund()
        await tracker._intialiaze()
        tracker.drawTable()

    if args.g == "y" or args.g == "o":
        tracker = MutualFund()
        await tracker._intialiaze()
        tracker.drawGraph()


async def main():
    choices = ["y", "n"]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        type=str,
        default="n",
        help="set whether to download new files",
        choices=choices,
    )
    parser.add_argument(
        "-g", type=str, default="n", help="draw a graph", choices=["y", "n", "o"]
    )
    parser.add_argument(
        "-t", type=str, default="y", help="Render the tables", choices=choices
    )
    parser.add_argument("-r", type=str, default="n", choices=["y", "n"])
    parser.add_argument("-dc", type=str, choices=choices, default="n")
    parser.add_argument(
        "-add", nargs="+", type=str, help="Mf unit amount date [dd-mon-yyyy]"
    )
    parser.add_argument("--logs", type=str, choices=["show", "clear", "n"], default="n")
    parser.add_argument("-logs", type=str, choices=["show", "clear", "n"], default="n")
    parser.add_argument("-dash", type=str, choices=["y", "n"], default="n")

    args = parser.parse_args()
    await callMutualFund(args)


if __name__ == "__main__":
    asyncio.run(main())

else:
    raise RuntimeError("this script is not meant to be imported")
