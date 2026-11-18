import subprocess


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


def active_window_linux():
    """
    id of the currently focused window
    """
    result = subprocess.run(
        ['xdotool', 'getactivewindow'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def flush_input_linux():
    """
    drop keystrokes/pastes that landed in this terminal
    so the shell does not run them after exit
    """
    import sys
    import termios

    if sys.stdin.isatty():
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
