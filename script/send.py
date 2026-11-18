import platform

#only import what works on this system (send_windows needs ctypes.WinDLL)
if platform.system() == "Windows":
    from script.send_windows import send_windows, active_window_windows, flush_input_windows
elif platform.system() == "Linux":
    from script.send_linux import send_linux, active_window_linux, flush_input_linux


class FocusLost(Exception):
    """
    focus left the target window -> abort transfer
    """


#window that receives the pastes, None = not locked yet
_target_window = None


def active_window():

    system = platform.system()

    if system == "Linux":
        return active_window_linux()
    elif system == "Windows":
        return active_window_windows()
    else:
        raise RuntimeError(
            f"Unsupported operating system: {platform.system()}"
        )


def lock_target_window():
    """
    remember the focused window (VNC)
    every following send() aborts if focus changed
    """

    global _target_window

    _target_window = active_window()


def flush_input():
    """
    drop input that was pasted into the local terminal by accident
    """

    system = platform.system()

    try:
        if system == "Linux":
            flush_input_linux()
        elif system == "Windows":
            flush_input_windows()
    except Exception:
        pass


def send(text):
    """
    puts text into clipboard and pastes it (ctrl+shift+v)
    """

    if _target_window is not None and active_window() != _target_window:
        raise FocusLost()

    system = platform.system()

    if system == "Linux":
        send_linux(text)
    elif system == "Windows":
        send_windows(text)
    else:
        raise RuntimeError(
            f"Unsupported operating system: {platform.system()}"
        )
