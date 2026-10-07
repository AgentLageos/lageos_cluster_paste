import ctypes
import time


# Windows API
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)



# BOOL
user32.OpenClipboard.argtypes = [ctypes.c_void_p]
user32.OpenClipboard.restype = ctypes.c_bool

user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = ctypes.c_bool

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = ctypes.c_bool


# HGLOBAL = Pointer-sized handle
kernel32.GlobalAlloc.argtypes = [
    ctypes.c_uint,
    ctypes.c_size_t
]
kernel32.GlobalAlloc.restype = ctypes.c_void_p

kernel32.GlobalLock.argtypes = [
    ctypes.c_void_p
]
kernel32.GlobalLock.restype = ctypes.c_void_p

kernel32.GlobalUnlock.argtypes = [
    ctypes.c_void_p
]
kernel32.GlobalUnlock.restype = ctypes.c_bool

kernel32.GlobalFree.argtypes = [
    ctypes.c_void_p
]
kernel32.GlobalFree.restype = ctypes.c_void_p


# SetClipboardData
user32.SetClipboardData.argtypes = [
    ctypes.c_uint,
    ctypes.c_void_p
]
user32.SetClipboardData.restype = ctypes.c_void_p



CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_V = 0x56

KEYEVENTF_KEYUP = 0x0002


# ------------------------------------------------------------
# Windows Clipboard + Paste
# ------------------------------------------------------------

def send_windows(text: str):


    data = text.encode("utf-16-le") + b"\x00\x00"


    if not user32.OpenClipboard(None):
        error = ctypes.get_last_error()

        raise RuntimeError(
            f"Could not open Windows clipboard "
            f"(error {error})"
        )

    h_global = None

    try:

        if not user32.EmptyClipboard():
            error = ctypes.get_last_error()

            raise RuntimeError(
                f"EmptyClipboard failed "
                f"(error {error})"
            )

        h_global = kernel32.GlobalAlloc(
            GMEM_MOVEABLE,
            len(data)
        )

        if not h_global:
            error = ctypes.get_last_error()

            raise MemoryError(
                f"GlobalAlloc failed "
                f"(error {error})"
            )

        p_global = kernel32.GlobalLock(
            h_global
        )

        if not p_global:
            error = ctypes.get_last_error()

            raise MemoryError(
                f"GlobalLock failed "
                f"(error {error})"
            )

        try:

            ctypes.memmove(
                p_global,
                data,
                len(data)
            )

        finally:

            kernel32.GlobalUnlock(
                h_global
            )

        result = user32.SetClipboardData(
            CF_UNICODETEXT,
            h_global
        )

        if not result:
            error = ctypes.get_last_error()

            raise RuntimeError(
                f"SetClipboardData failed "
                f"(error {error})"
            )


        h_global = None

    finally:

        if h_global:
            kernel32.GlobalFree(h_global)

        user32.CloseClipboard()


    time.sleep(0.05)


    user32.keybd_event(
        VK_CONTROL,
        0,
        0,
        0
    )

    user32.keybd_event(
        VK_SHIFT,
        0,
        0,
        0
    )

    user32.keybd_event(
        VK_V,
        0,
        0,
        0
    )

    user32.keybd_event(
        VK_V,
        0,
        KEYEVENTF_KEYUP,
        0
    )

    user32.keybd_event(
        VK_SHIFT,
        0,
        KEYEVENTF_KEYUP,
        0
    )

    user32.keybd_event(
        VK_CONTROL,
        0,
        KEYEVENTF_KEYUP,
        0
    )
