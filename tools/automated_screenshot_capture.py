import os
import subprocess
import time
import ctypes
from ctypes import wintypes
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

exe = os.path.join(os.environ['TEMP'], 'vbam', 'visualboyadvance-m.exe')
rom = os.path.abspath('pilot.gba')

os.makedirs('screenshots/greek_pilot_cutscene', exist_ok=True)
proc = subprocess.Popen([exe, rom], cwd=os.getcwd())
time.sleep(3.5)

found_hwnd = []
def enum_cb(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        buff = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buff, 256)
        if 'VisualBoyAdvance' in buff.value:
            found_hwnd.append(hwnd)
    return True
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
hwnd = found_hwnd[0]

wx_canvas = []
def enum_child(h, lparam):
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, cls, 256)
    if cls.value == 'wxWindow':
        wx_canvas.append(h)
    return True
EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumChildWindows(hwnd, EnumChildProc(enum_child), 0)
canvas = wx_canvas[0]

def capture(fn):
    rect = wintypes.RECT()
    user32.GetClientRect(canvas, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    hwndDC = user32.GetDC(canvas)
    mfcDC = gdi32.CreateCompatibleDC(hwndDC)
    bmp = gdi32.CreateCompatibleBitmap(hwndDC, w, h)
    gdi32.SelectObject(mfcDC, bmp)
    user32.PrintWindow(canvas, mfcDC, 2)
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
                    ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
                    ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]
    bmi = BITMAPINFOHEADER()
    bmi.biSize, bmi.biWidth, bmi.biHeight, bmi.biPlanes, bmi.biBitCount = ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mfcDC, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    img.save(fn)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mfcDC)
    user32.ReleaseDC(canvas, hwndDC)
    print(f"Captured {fn}")

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_RETURN = 0x0D
VK_L = 0x4C

def send_key(vk, hold=0.08, wait=0.25):
    user32.PostMessageW(canvas, WM_KEYDOWN, vk, 0)
    time.sleep(hold)
    user32.PostMessageW(canvas, WM_KEYUP, vk, 0)
    time.sleep(wait)

print('1. Starting game setup...')
send_key(VK_RETURN, wait=1.0)
send_key(VK_L, wait=2.5)

# Char Name
send_key(VK_L, wait=0.3)
send_key(VK_RETURN, wait=0.6)
send_key(VK_L, wait=1.5)

# Birthday
send_key(VK_L, wait=0.3)
send_key(VK_L, wait=0.3)
send_key(VK_RETURN, wait=0.6)
send_key(VK_L, wait=1.5)

# Dog Name
send_key(VK_L, wait=0.3)
send_key(VK_RETURN, wait=0.6)
send_key(VK_L, wait=1.5)

# Farm Name
send_key(VK_L, wait=0.3)
send_key(VK_RETURN, wait=0.6)
send_key(VK_L, wait=2.5)

print('2. Arriving on farm and advancing through Thomas...')
time.sleep(5.0)

# 35 presses through Thomas dialogue
for p in range(35):
    send_key(VK_L, wait=0.5)

print('3. Thomas dialogue complete. Entering Flashback Cutscene!')
time.sleep(2.0)

# Capture the flashback cutscene!
# In the cutscene, text prints character by character, then pauses.
# We will capture at steady intervals, advancing dialogue with L.
for i in range(1, 40):
    time.sleep(1.2)
    fn = f'screenshots/greek_pilot_cutscene/greek_scene_{i:02d}.png'
    capture(fn)
    send_key(VK_L, wait=0.3)

proc.terminate()
print('All Greek cutscene captures complete!')
