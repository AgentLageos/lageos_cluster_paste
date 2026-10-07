import os
import sys
import time
import base64
import subprocess
import platform
from pathlib import Path
from script.validate_config import validate_config
from script.load_config import load_config
from script.check_args import check_args
if platform.system() == "Windows":
    from script.send_windows import send_windows

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
    paste_delay: float
):
    """
    transfers single file
    relative path will be kept
    """

    path_to_file = os.path.abspath(path_to_file)
    base_path = os.path.abspath(base_path)

    relative_path = Path(
        os.path.relpath(path_to_file, base_path)
    )

    remote_file = relative_path.as_posix()

    remote_b64 = remote_file + ".b64"

    #create target dir
    remote_dir = os.path.dirname(remote_file)

    if remote_dir:
        send(
            f"mkdir -p -- '{remote_dir}'\n"
        )

        time.sleep(0.2)
    
    #create file info


    file_size = os.path.getsize(path_to_file)

    print()
    print("=" * 70)
    print(f"File: {relative_path}")
    print(f"Size: {file_size:,} bytes")
    print("=" * 70)

    #temp base64
    
    send(
        f"> '{remote_b64}'\n"
    )

    time.sleep(0.5)

    #read and send in chunks
    sent = 0
    chunk_number = 0

    with open(path_to_file, "rb") as f:

        while True:

            raw = f.read(chunk_size)

            if not raw:
                break

            part = base64.b64encode(raw).decode("ascii")

            send(
                f"printf '%s' '{part}' >> '{remote_b64}'\n"
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

    print()


    #reconvert from base64
    send(
        f"base64 -d '{remote_b64}' > '{remote_file}'\n"
    )

    time.sleep(0.5)

    #delete tmp files
    send(
        f"rm -f -- '{remote_b64}'\n"
    )

    time.sleep(0.5)

    print(
        f"Transferred: {relative_path}"
    )


#args

def check_args():

    if len(sys.argv) != 2:

        print(
            f"Usage: {sys.argv[0]} <file-or-directory>"
        )

        print()
        print("Examples:")
        print(
            f"  {sys.argv[0]} file.txt"
        )
        print(
            f"  {sys.argv[0]} ./my_project"
        )

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


# ============================================================
# Main
# ============================================================

def main():


    path_to_config = "script/config.yml"

    validate_config(path_to_config)

    config = load_config(path_to_config)

    chunk_size = config["chunk_size"]
    paste_delay = config["paste_delay"]

    print(
        f"Configured chunk size: {chunk_size}"
    )

    print(
        f"Paste delay: {paste_delay}s"
    )


    source = check_args()

    print()
    print(f"Source: {source}")


    files = collect_files(source)

    if not files:

        print(
            "ERROR: No files found."
        )

        sys.exit(1)

    print()
    print(
        f"Found {len(files)} file(s):"
    )

    for file in files:
        print(
            f"  {file}"
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

    if os.path.isfile(source):

        base_path = os.path.dirname(source)

    else:

        base_path = os.path.dirname(source)

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

    for file in files:

        transfer_file(
            path_to_file=file,
            base_path=base_path,
            chunk_size=RAW_chunk_size,
            paste_delay=paste_delay
        )

    send(
        'echo "DONE"\n'
    )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
