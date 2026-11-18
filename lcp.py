import os
import sys
import time
from script.validate_config import validate_config
from script.load_config import load_config
from script.check_args import check_args
from script.collect_files import collect_files
from script.send import send, lock_target_window, flush_input, FocusLost
from script.state import select_changed_files, save_state
from script.manifest import save_manifest, load_retry_files
from script.transfer import clear_remote_logs, transfer_file, send_summary, Progress

#realpath: also works when called via symlink
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


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
    exclude_git = config.get("exclude_git", True)

    print(
        f"Configured chunk size: {chunk_size}"
    )

    print(
        f"Paste delay: {paste_delay}s"
    )

    print(
        f"Retry hint: {'on' if retry_hint else 'off'}"
    )

    print(
        f"Exclude git files: {'on' if exclude_git else 'off'}"
    )


    source, retry_numbers, force = check_args()

    #only set for dirs, saved after transfer
    new_state = None

    if retry_numbers is None:

        print()
        print(f"Source: {source}")

        files = collect_files(source, exclude_git)

        #file: lands directly in remote cwd
        #dir: dir itself is recreated in remote cwd
        base_path = os.path.dirname(source)

        if os.path.isdir(source) and files:

            files, new_state = select_changed_files(source, files, force)

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
    print("(to abort: click any other window, e.g. this terminal)")

    #from now on every paste checks that the VNC window still has focus
    lock_target_window()

    try:
        run_transfer(files, base_path, RAW_chunk_size, paste_delay, retry_hint)

    except (FocusLost, KeyboardInterrupt):

        flush_input()

        print()
        print()
        print("=" * 70)
        print("ABORTED")
        print("=" * 70)
        print("The file being sent is incomplete on the remote side.")
        print("Nothing was saved, the next run sends the same files again.")

        sys.exit(1)

    if new_state is not None:
        save_state(source, new_state)

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


def run_transfer(files, base_path, RAW_chunk_size, paste_delay, retry_hint):

    clear_remote_logs(paste_delay)

    progress = Progress(
        total_files=len(files),
        total_bytes=sum(os.path.getsize(file) for file in files)
    )

    for number, file in enumerate(files, start=1):

        transfer_file(
            path_to_file=file,
            base_path=base_path,
            chunk_size=RAW_chunk_size,
            paste_delay=paste_delay,
            index=number,
            retry_hint=retry_hint,
            progress=progress
        )

    send('clear\n')
    time.sleep(paste_delay)

    send_summary(retry_hint)


if __name__ == "__main__":
    main()
