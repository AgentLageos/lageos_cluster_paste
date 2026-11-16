import os
import sys
import time
import base64
import subprocess
import platform
import shlex
import json
import hashlib
from pathlib import Path
from script.validate_config import validate_config
from script.load_config import load_config
if platform.system() == "Windows":
    from script.send_windows import send_windows

#realpath: also works when called via symlink
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

#local list of last transfer, used by --retry
MANIFEST_FILE = os.path.join(SCRIPT_DIR, ".lcp_last_run.json")

#remote logs, collected during transfer, shown at the end
REMOTE_FAILED = ".lcp_failed"
REMOTE_RETRY = ".lcp_retry"

#stored inside a transferred dir: what was sent last time (path -> sha256)
#never transferred itself
STATE_FILE_NAME = ".lcp_state.json"

def send_linux(text):
    p = subprocess.Popen(
        ['xclip', '-selection', 'clipboard'],
        stdin=subprocess.PIPE
    )
    p.communicate(input=text.encode())

    subprocess.run([
        'xdotool',
        'key',
        '--clearmodifiers',
        'ctrl+shift+v'
    ])

def send(text):

    system = platform.system()

    if system == "Linux":
        send_linux(text)
    elif system == "Windows":
        send_windows(text)
    else:
        raise RuntimeError(
            f"Unsupported operating system: {platform.system()}"
        )





def collect_files(source):
    """
    collects to files to be transfered
    could be files or dirs
    searches recursivly
    """

    source = os.path.abspath(source)

    if not os.path.exists(source):
        raise FileNotFoundError(
            f"Source does not exist: {source}"
        )

    if os.path.isfile(source):
        return [source]

    if os.path.isdir(source):
        files = []

        for root, dirs, filenames in os.walk(source):
            for filename in filenames:
                if filename == STATE_FILE_NAME:
                    continue
                files.append(
                    os.path.join(root, filename)
                )

        files.sort()

        return files

    raise ValueError(
        f"Unsupported source: {source}"
    )


def transfer_file(
    path_to_file: str,
    base_path: str,
    chunk_size: int,
    paste_delay: float,
    index: int,
    retry_hint: bool
):
    """
    transfers single file
    relative path will be kept
    remote side verifies sha256 and logs failures
    """

    path_to_file = os.path.abspath(path_to_file)
    base_path = os.path.abspath(base_path)

    relative_path = Path(
        os.path.relpath(path_to_file, base_path)
    )

    remote_file = relative_path.as_posix()

    remote_b64 = remote_file + ".b64"

    #quote for remote shell (handles spaces, quotes, etc.)
    q_file = shlex.quote(remote_file)
    q_b64 = shlex.quote(remote_b64)

    #create target dir
    remote_dir = os.path.dirname(remote_file)

    clear_counter = 0

    if remote_dir:
        send(
            f"mkdir -p -- {shlex.quote(remote_dir)}\n"
        )

        time.sleep(paste_delay)
    
    #create file info
    file_size = os.path.getsize(path_to_file)

    print()
    print("=" * 70)
    print(f"File: {relative_path}")
    print(f"Size: {file_size:,} bytes")
    print("=" * 70)

    #temp base64
    
    send(
        f"> {q_b64}\n"
    )

    time.sleep(paste_delay)

    #read and send in chunks
    sent = 0
    chunk_number = 0
    sha256 = hashlib.sha256()

    with open(path_to_file, "rb") as f:

        while True:

            raw = f.read(chunk_size)

            if not raw:
                break

            sha256.update(raw)

            part = base64.b64encode(raw).decode("ascii")

            send(
                f"printf '%s' '{part}' >> {q_b64}\n"
            )

            sent += len(raw)
            chunk_number += 1

            if file_size > 0:
                progress = sent / file_size * 100
            else:
                progress = 100.0

            print(
                f"\rChunk {chunk_number} | "
                f"{sent:,} / {file_size:,} bytes "
                f"({progress:6.2f}%)",
                end="",
                flush=True
            )

            time.sleep(paste_delay)

            clear_counter += 1
            if (clear_counter>=10):
                send('clear\n')
                time.sleep(paste_delay)
                clear_counter = 0

    print()


    #reconvert from base64
    send(
        f"base64 -d {q_b64} > {q_file}\n"
    )

    time.sleep(paste_delay)

    #verify on remote side
    #(no feedback channel, so failures are logged remotely and shown at the end)
    #missing file or missing sha256sum also counts as failure
    on_fail = f"echo {q_file} >> {REMOTE_FAILED}"

    if retry_hint:
        on_fail += f"; echo {index} >> {REMOTE_RETRY}"

    send(
        f"[ \"$(sha256sum < {q_file})\" = "
        f"'{sha256.hexdigest()}  -' ] || {{ {on_fail}; }}\n"
    )

    time.sleep(paste_delay)

    #delete tmp files
    send(
        f"rm -f -- {q_b64}\n"
    )


    time.sleep(paste_delay)
    send('clear\n')

    time.sleep(paste_delay)

    print(
        f"Transferred: {relative_path}"
    )


#args

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


#state of transferred dirs

def file_sha256(path):

    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
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


#manifest

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


# ============================================================
# Main
# ============================================================

def main():


    path_to_config = os.path.join(
        SCRIPT_DIR,
        "script",
        "config.yml"
    )

    validate_config(path_to_config)

    config = load_config(path_to_config)

    chunk_size = config["chunk_size"]
    paste_delay = config["paste_delay"]
    retry_hint = config.get("retry_hint", True)

    print(
        f"Configured chunk size: {chunk_size}"
    )

    print(
        f"Paste delay: {paste_delay}s"
    )

    print(
        f"Retry hint: {'on' if retry_hint else 'off'}"
    )


    source, retry_numbers, force = check_args()

    #only set for dirs, saved after transfer
    new_state = None

    if retry_numbers is None:

        print()
        print(f"Source: {source}")

        files = collect_files(source)

        #file: lands directly in remote cwd
        #dir: dir itself is recreated in remote cwd
        base_path = os.path.dirname(source)

        if os.path.isdir(source) and files:

            rel_paths = {
                file: Path(os.path.relpath(file, source)).as_posix()
                for file in files
            }

            new_state = {
                rel_paths[file]: file_sha256(file)
                for file in files
            }

            if force:

                print("--force: sending all files.")

            else:

                old_state = load_state(source)

                files = [
                    file for file in files
                    if old_state.get(rel_paths[file])
                    != new_state[rel_paths[file]]
                ]

                print(
                    f"Unchanged since last transfer: "
                    f"{len(new_state) - len(files)} file(s)"
                )

                if not files:

                    save_state(source, new_state)

                    print()
                    print("Nothing changed, nothing to send.")
                    print("(use --force to send everything again)")

                    sys.exit(0)

    else:

        print()
        print(f"Retrying file(s): {' '.join(map(str, retry_numbers))}")

        base_path, files = load_retry_files(retry_numbers)

    if not files:

        print(
            "ERROR: No files found."
        )

        sys.exit(1)

    print()
    print(
        f"Found {len(files)} file(s):"
    )

    for number, file in enumerate(files, start=1):
        print(
            f"  {number:>3}  {file}"
        )

    # --------------------------------------------------------
    # Base64 chunk size
    #
    # chunk_size = maximum amount of Base64-chars
    #
    # 4 Base64 chars = 3 Bytes
    #
    # therefor:
    #
    # RAW_chunk_size = floor(chunk_size / 4) * 3
    # --------------------------------------------------------

    RAW_chunk_size = (
        chunk_size // 4
    ) * 3

    if RAW_chunk_size <= 0:

        raise ValueError(
            "chunk_size is too small. "
            "It must be at least 4."
        )

    print()
    print(
        f"Base64 chunk size: "
        f"{chunk_size} chars"
    )

    print(
        f"Raw chunk size: "
        f"{RAW_chunk_size} bytes"
    )

    if retry_hint:
        save_manifest(base_path, files)

    send("\n")

    print()
    print(
        "Switch NOW to VNC Window..."
    )

    for i in range(5, 0, -1):

        print(i)

        time.sleep(1)

    print()
    print("Starting...")

    #remove logs of earlier runs
    send(
        f"rm -f -- {REMOTE_FAILED} {REMOTE_RETRY}\n"
    )

    time.sleep(paste_delay)

    for number, file in enumerate(files, start=1):

        transfer_file(
            path_to_file=file,
            base_path=base_path,
            chunk_size=RAW_chunk_size,
            paste_delay=paste_delay,
            index=number,
            retry_hint=retry_hint
        )

    send('clear\n')
    time.sleep(paste_delay)

    #summary on remote side
    on_fail = f'echo "FAILED:"; cat {REMOTE_FAILED}'

    if retry_hint:
        on_fail += (
            f'; echo; echo "Re-send with:"; '
            f'echo "python lcp.py --retry" $(cat {REMOTE_RETRY})'
        )

    send(
        f'if [ -s {REMOTE_FAILED} ]; then {on_fail}; '
        f'else echo "DONE - ALL OK"; fi; '
        f'rm -f -- {REMOTE_FAILED} {REMOTE_RETRY}\n'
    )


    if new_state is not None:
        save_state(source, new_state)

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
