import os
import json
import hashlib
from pathlib import Path

from script.read_file_chunks import read_file_chunks

#stored inside a transferred dir: what was sent last time (path -> sha256)
#never transferred itself
STATE_FILE_NAME = ".lcp_state.json"


def file_sha256(path):

    sha256 = hashlib.sha256()

    for block in read_file_chunks(path, 1024 * 1024):
        sha256.update(block)

    return sha256.hexdigest()


def load_state(source_dir):
    """
    returns {relative path: sha256} of last transfer, empty if none
    """

    state_file = os.path.join(source_dir, STATE_FILE_NAME)

    if not os.path.isfile(state_file):
        return {}

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)["files"]
    except (ValueError, KeyError):
        print(
            f"WARNING: Unreadable {STATE_FILE_NAME}, "
            f"sending all files."
        )
        return {}


def save_state(source_dir, hashes):

    state_file = os.path.join(source_dir, STATE_FILE_NAME)

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(
            {"files": hashes},
            f,
            indent=2,
            sort_keys=True
        )


def select_changed_files(source_dir, files, force):
    """
    compares files with state of last transfer
    returns (files to send, new state)
    new state should only be saved after transfer
    """

    rel_paths = {
        file: Path(os.path.relpath(file, source_dir)).as_posix()
        for file in files
    }

    new_state = {
        rel_paths[file]: file_sha256(file)
        for file in files
    }

    if force:

        print("--force: sending all files.")

        return files, new_state

    old_state = load_state(source_dir)

    changed = [
        file for file in files
        if old_state.get(rel_paths[file])
        != new_state[rel_paths[file]]
    ]

    print(
        f"Unchanged since last transfer: "
        f"{len(files) - len(changed)} file(s)"
    )

    return changed, new_state
