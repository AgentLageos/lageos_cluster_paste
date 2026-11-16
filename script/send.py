import platform

#only import what works on this system (send_windows needs ctypes.WinDLL)
if platform.system() == "Windows":
    from script.send_windows import send_windows
elif platform.system() == "Linux":
    from script.send_linux import send_linux


def send(text):
    """
    puts text into clipboard and pastes it (ctrl+shift+v)
    """

    system = platform.system()

    if system == "Linux":
        send_linux(text)
    elif system == "Windows":
        send_windows(text)
    else:
        raise RuntimeError(
            f"Unsupported operating system: {platform.system()}"
        )
