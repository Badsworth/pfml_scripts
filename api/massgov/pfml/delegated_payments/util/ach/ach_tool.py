#
# Command line tool for ACH file operations.
#
# Example usage:
#   poetry run ach-reader tests/delegated_payments/util/ach/test_files/PUBACHRTRN__scrambled.txt
#

import argparse

import massgov.pfml.util.logging

from . import reader

logger = massgov.pfml.util.logging.get_logger(__name__)


def ach_reader():
    """Read an ACH file using the ACHReader class."""
    massgov.pfml.util.logging.init("ach_reader")

    args = parse_args()

    for file in args.file:
        print("========== %s ==========\n" % file)

        stream = open(file, mode="r", newline=None)
        ach = reader.ACHReader(stream)

        print("ACH RETURNS (%i total)\n" % len(ach.get_ach_returns()))
        for ach_return in ach.get_ach_returns():
            print("    %r" % ach_return)
        print("\n")

        print("CHANGE NOTIFICATIONS (%i total)\n" % len(ach.get_change_notifications()))
        for change_notification in ach.get_change_notifications():
            print("    %r" % change_notification)
        print("\n")

        print("WARNINGS (%i total)\n" % len(ach.get_warnings()))
        for warning in ach.get_warnings():
            print("    %r" % warning)
        print("\n\n")


def parse_args():
    """Parse command line arguments and flags."""
    parser = argparse.ArgumentParser(description="ACH file reader",)
    parser.add_argument("file", nargs="+", help="ACH files")
    args = parser.parse_args()
    if not args.file:
        parser.print_help()
        exit(1)
    return args
