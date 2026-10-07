import ctypes
import time


def send_windows(text):
    # Windows API
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    # Clipboard öffnen
    if not user32.OpenClipboard(None):
        raise RuntimeError("Could not open Windows clipboard")

    try:
        # Altes Clipboard löschen
        user32.EmptyClipboard()

        # Python string -> UTF-16
        data = text.encode("utf-16-le") + b"\x00\x00"

        # Global memory reservieren
        h_global = kernel32.GlobalAlloc(
            GMEM_MOVEABLE,
            len(data)
        )

        if not h_global:
            raise MemoryError("GlobalAlloc failed")

        try:
            # Speicher locken
            p_global = kernel32.GlobalLock(h_global)

            if not p_global:
                raise MemoryError("GlobalLock failed")

            try:
                ctypes.memmove(
                    p_global,
                    data,
                    len(data)
                )

            finally:
                kernel32.GlobalUnlock(h_global)

            # Clipboard übernimmt den Speicher
            if not user32.SetClipboardData(
                CF_UNICODETEXT,
                h_global
            ):
                raise RuntimeError(
                    "SetClipboardData failed"
                )

            # Wichtig:
            # Nach erfolgreichem SetClipboardData darf
            # h_global nicht mehr freigegeben werden.
            h_global = None

        finally:
            if h_global:
                kernel32.GlobalFree(h_global)

    finally:
        user32.CloseClipboard()

    # Kurze Pause, damit Windows/VNC das Clipboard
    # übernehmen kann.
    time.sleep(0.05)

    # Ctrl+Shift+V senden
    VK_CONTROL = 0x11
    VK_SHIFT = 0x10
    VK_V = 0x56

    KEYEVENTF_KEYUP = 0x0002

    user32.keybd_event(
        VK_CONTROL, 0, 0, 0
    )
    user32.keybd_event(
        VK_SHIFT, 0, 0, 0
    )
    user32.keybd_event(
        VK_V, 0, 0, 0
    )

    user32.keybd_event(
        VK_V, 0, KEYEVENTF_KEYUP, 0
    )
    user32.keybd_event(
        VK_SHIFT, 0, KEYEVENTF_KEYUP, 0
    )
    user32.keybd_event(
        VK_CONTROL, 0, KEYEVENTF_KEYUP, 0
    )
