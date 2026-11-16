import os
import sys


def print_usage():

    print(
        f"Usage: {sys.argv[0]} [--force] <file-or-directory>"
    )
    print(
        f"       {sys.argv[0]} --retry <number> [<number> ...]"
    )
    print()
    print(
        "  Directories: only files changed since the last transfer are sent."
    )
    print(
        "  --force: send all files again."
    )

    print()
    print("Examples:")
    print(
        f"  {sys.argv[0]} file.txt"
    )
    print(
        f"  {sys.argv[0]} ./my_project"
    )
    print(
        f"  {sys.argv[0]} --force ./my_project"
    )
    print(
        f"  {sys.argv[0]} --retry 3 7"
    )


def check_args():
    """
    returns (source, None, force) for normal run
    returns (None, [numbers], False) for --retry
    """

    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == "--retry":

        try:
            numbers = [int(n) for n in args[1:]]
        except ValueError:
            print("ERROR: --retry expects file numbers.")
            sys.exit(1)

        return None, numbers, False

    force = "--force" in args

    if force:
        args.remove("--force")

    if len(args) != 1 or args[0].startswith("--"):

        print_usage()

        sys.exit(1)

    source = os.path.abspath(
        args[0]
    )

    if not os.path.exists(source):

        print(
            f"ERROR: Source does not exist:"
            f"\n{source}"
        )

        sys.exit(1)

    return source, None, force
