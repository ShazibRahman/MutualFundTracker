"""
This script provides a command-line interface (CLI) for managing mutual funds.
It allows users to perform various operations such as adding orders, viewing logs,
clearing logs, rendering tables, drawing graphs, and more.
"""

import argparse
import asyncio
import os

from decorator_utils import LockManager

import logs.log_config as log_config  # pylint: disable=unused-import # import log  # noqa: F401 # noqa: all
from MutualFundTracker import MutualFund, lock_file

git_dir = os.path.dirname(__file__)
index_path = os.path.join(git_dir, "dashBoard", "index.py")
logger_path = os.path.join(git_dir, "logs", "logger.log")
ANACRON_USER = "Shazib_Anacron"


def read_logs():
    """Read the logs using bat."""
    os.system(f"bat --paging=never {logger_path}")


def clear_logs():
    """Clear the logs."""
    with open(logger_path, "w", encoding="utf-8") as file_:
        file_.truncate()


async def handle_logs(args):
    """Handle log-related commands."""
    if args.logs == "show":
        read_logs()
    elif args.logs == "clear":
        clear_logs()


async def handle_tracker_operations(args, tracker):
    """Handle operations related to the mutual fund tracker."""
    if args.add:
        tracker.add_order(
            args.add[0], float(args.add[1]), float(args.add[2]), args.add[3]
        )
    elif args.dc == "y":
        await tracker.day_change_table()
    elif args.ic == "y":
        tracker.draw_graph_current_vs_invested()
    elif args.r == "y":
        await tracker.get_current_values()
        tracker.draw_table()
    elif args.d == "y":
        await tracker.get_current_values()
        tracker.draw_table()
    elif args.dash == "y":
        os.system(f"/home/shazib/Desktop/linux/test/bin/python {index_path}")
    elif args.g != "o":
        tracker.draw_table()
    if args.g in ["y", "o"]:
        tracker.draw_graph()


async def call_mutual_fund(args) -> None:  # pragma: no cover
    """Call the mutual fund tracker."""
    if args.logs in ["show", "clear"]:
        await handle_logs(args)
        return

    with LockManager(lock_file) as lock_acquired:
        if not lock_acquired:
            return

        async with MutualFund(args.d == "y") as tracker:
            await handle_tracker_operations(args, tracker)


async def main():
    """Main function."""
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
    parser.add_argument("-r", type=str, default="n", choices=choices)
    parser.add_argument("-dc", type=str, choices=choices, default="n")
    parser.add_argument(
        "-add", nargs="+", type=str, help="Mf unit amount date [dd-mon-yyyy]"
    )
    parser.add_argument("--logs", type=str, choices=["show", "clear", "n"], default="n")
    parser.add_argument("-dash", type=str, choices=choices, default="n")
    parser.add_argument("-ic", type=str, choices=choices, default="n")

    args = parser.parse_args()
    await call_mutual_fund(args)


if __name__ == "__main__":
    asyncio.run(main())
else:
    raise RuntimeError("This script is not meant to be imported")
