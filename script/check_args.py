import os
import sys

def check_args():

    if len(sys.argv) != 2:

        print(f"Usage: {sys.argv[0]} <file-or-directory>")

        print()
        print("Examples:")
        print(f"  {sys.argv[0]} file.txt")
        print(f"  {sys.argv[0]} ./my_project")

        sys.exit(1)

    source = os.path.abspath(
        sys.argv[1]
    )

    if not os.path.exists(source):

        print(
            f"ERROR: Source does not exist:"
            f"\n{source}"
        )

        sys.exit(1)

    return source

