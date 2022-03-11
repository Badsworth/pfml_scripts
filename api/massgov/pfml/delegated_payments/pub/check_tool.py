#
# Command line tool for check payment file operations.
#
# Example usage:
#   poetry run check-reader tests/delegated_payments/util/check/test_files/PUBACHRTRN__scrambled.txt
#

import argparse

import massgov.pfml.util.logging

from . import check_return

logger = massgov.pfml.util.logging.get_logger(__name__)


def check_reader():
    """Read an check payment return file using the CheckReader class."""
    massgov.pfml.util.logging.init("check_reader")

    args = parse_args()

    for file in args.file:
        print("========== %s ==========\n" % file)

        stream = open(file, mode="r", newline=None)
        reader = check_return.CheckReader(stream)

        print("CHECK PAYMENTS (%i total)\n" % len(reader.get_check_payments()))
        for check_payment in reader.get_check_payments():
            print("    %r" % check_payment)
        print("\n")

        print("LINE ERRORS (%i total)\n" % len(reader.get_line_errors()))
        for line_error in reader.get_line_errors():
            print("    %r" % line_error)
        print("\n\n")


def parse_args():
    """Parse command line arguments and flags."""
    parser = argparse.ArgumentParser(description="Check return file reader")
    parser.add_argument("file", nargs="+", help="Check return files")
    args = parser.parse_args()
    if not args.file:
        parser.print_help()
        exit(1)
    return args
