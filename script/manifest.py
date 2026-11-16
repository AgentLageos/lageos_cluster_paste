import os
import sys
import json

#local list of last transfer, used by --retry
#lives in repo root, realpath: also works when lcp.py is called via symlink
MANIFEST_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    ".lcp_last_run.json"
)


def save_manifest(base_path, files):
    """
    remembers transferred files, numbers in remote retry hint refer to this
    """

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"base_path": base_path, "files": files},
            f,
            indent=2
        )


def load_retry_files(numbers):
    """
    picks files of last run by number (1-based)
    returns (base_path, files)
    """

    if not os.path.isfile(MANIFEST_FILE):
        print(
            f"ERROR: No previous run found:"
            f"\n{MANIFEST_FILE}"
        )
        sys.exit(1)

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    last_files = manifest["files"]
    files = []

    for n in numbers:

        if not 1 <= n <= len(last_files):
            print(
                f"ERROR: No file number {n} in last run "
                f"(1-{len(last_files)})."
            )
            sys.exit(1)

        file = last_files[n - 1]

        if not os.path.isfile(file):
            print(
                f"ERROR: File no longer exists:"
                f"\n{file}"
            )
            sys.exit(1)

        if file not in files:
            files.append(file)

    return manifest["base_path"], files
