import argparse
import asyncio
import os

from MutualFundTracker import MutualFund

git_dir = os.path.dirname(__file__)
index_path = f"{os.path.dirname(__file__)}/dashBoard/index.py"
loggerPath = f"{os.path.dirname(__file__)}/logs/logger.log"
ANACRON_USER = "Shazib_Anacron"


# sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())


def read_logs():
    """
    Read the logs using bat
    :return:
    """
    os.system(f"bat --paging=never {loggerPath}")


def clear_logs():
    """
    Clear the logs
    :return:
    """
    with open(loggerPath, "w", encoding="utf-8") as file_:
        file_.truncate()


async def call_mutual_fund(args) -> None:  # pragma: no cover
    """
    Call the mutual fund tracker
    :param args:
    :return:
    """
    if args.logs == "show":
        read_logs()
        return

    if args.logs == "clear":
        clear_logs()
        return
    async with MutualFund(args.d == 'y') as tracker:

        if args.add is not None:
            tracker.addOrder(
                args.add[0], float(args.add[1]), float(args.add[2]), args.add[3]
            )
            return
        if args.dc == "y":
            await tracker.day_change_table()
            return

        if args.r == "y":
            await tracker.get_current_values()
            tracker.draw_table()
            return

        if args.d == "y":
            await tracker.get_current_values()
            tracker.draw_table()

            return
        if args.dash == "y":
            os.system(f"/home/shazib/Desktop/linux/test/bin/python {index_path}")
            return

        if args.g != "o":
            tracker.draw_table()

        if args.g in ["y", "o"]:
            tracker.draw_graph()


async def main():
    """
    Main function
    :return:
    """
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
    parser.add_argument("-dash", type=str, choices=["y", "n"], default="n")

    args = parser.parse_args()
    await call_mutual_fund(args)


if __name__ == "__main__":
    asyncio.run(main())

else:
    raise RuntimeError("this script is not meant to be imported")
