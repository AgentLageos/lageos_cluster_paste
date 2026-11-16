import os
import time
import base64
import shlex
import hashlib
from pathlib import Path

from script.send import send
from script.read_file_chunks import read_file_chunks

#remote logs, collected during transfer, shown at the end
REMOTE_FAILED = ".lcp_failed"
REMOTE_RETRY = ".lcp_retry"

BAR_WIDTH = 30


def format_duration(seconds):
    """
    seconds -> 1h02m03s / 2m03s / 3s
    """

    seconds = int(seconds)

    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)

    if hours:
        return f"{hours}h{minutes:02d}m{seconds:02d}s"

    if minutes:
        return f"{minutes}m{seconds:02d}s"

    return f"{seconds}s"


class Progress:
    """
    overall progress over all files of one run
    """

    def __init__(self, total_files, total_bytes):

        self.total_files = total_files
        self.total_bytes = total_bytes
        self.done_bytes = 0
        self.start = time.monotonic()

    def show(self, index, file_sent, file_size):

        done = self.done_bytes + file_sent

        if self.total_bytes > 0:
            fraction = done / self.total_bytes
        else:
            fraction = 1.0

        if file_size > 0:
            file_progress = file_sent / file_size * 100
        else:
            file_progress = 100.0

        filled = int(fraction * BAR_WIDTH)
        bar = "#" * filled + "-" * (BAR_WIDTH - filled)

        elapsed = time.monotonic() - self.start

        #estimate from average speed so far
        if 0 < fraction < 1:
            eta = format_duration(elapsed / fraction - elapsed)
        elif fraction >= 1:
            eta = "0s"
        else:
            eta = "?"

        print(
            f"\r[{index}/{self.total_files}] "
            f"[{bar}] {fraction * 100:6.2f}% | "
            f"file {file_progress:6.2f}% | "
            f"elapsed {format_duration(elapsed)} | "
            f"ETA {eta}   ",
            end="",
            flush=True
        )

    def finish_file(self, file_size):

        self.done_bytes += file_size


def clear_remote_logs(paste_delay):
    """
    remove logs of earlier runs
    """

    send(
        f"rm -f -- {REMOTE_FAILED} {REMOTE_RETRY}\n"
    )

    time.sleep(paste_delay)


def transfer_file(
    path_to_file: str,
    base_path: str,
    chunk_size: int,
    paste_delay: float,
    index: int,
    retry_hint: bool,
    progress: Progress
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
    print(f"File {index}/{progress.total_files}: {relative_path}")
    print(f"Size: {file_size:,} bytes")
    print("=" * 70)

    #temp base64

    send(
        f"> {q_b64}\n"
    )

    time.sleep(paste_delay)

    #read and send in chunks
    sent = 0
    sha256 = hashlib.sha256()

    progress.show(index, sent, file_size)

    for raw in read_file_chunks(path_to_file, chunk_size):

        sha256.update(raw)

        part = base64.b64encode(raw).decode("ascii")

        send(
            f"printf '%s' '{part}' >> {q_b64}\n"
        )

        sent += len(raw)

        progress.show(index, sent, file_size)

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

    progress.finish_file(file_size)

    print(
        f"Transferred: {relative_path}"
    )


def send_summary(retry_hint):
    """
    shows result of all verifications on remote side
    """

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
