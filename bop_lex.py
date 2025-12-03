from pynput import keyboard, mouse
from PIL import Image, ImageTk
import tkinter as tk
import random
import os
import sys  # needed to detect PyInstaller exe

# static config
TRANSPARENT = "magenta"
HIT_MS = 120        # how long hit-frame shows
LOOP_MS = 20        # GUI loop interval

# runtime state
pending = False     # hit triggered?
hits = 0            # counter
scale = 0.4         # image scale factor

# base folder:
# - in .py: folder of this file
# - in .exe (PyInstaller --onefile): folder of the exe
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# textures live in ./Textures relative to base dir
TEXTURE_DIR = os.path.join(BASE_DIR, "Textures")


# input callback
def on_any_input(*_):
    global pending, hits
    hits += 1
    pending = True


# global listeners
kb = keyboard.Listener(on_press=on_any_input)
ms = mouse.Listener(on_click=on_any_input)
kb.start()
ms.start()

# transparent window
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.config(bg=TRANSPARENT)
root.attributes("-transparentcolor", TRANSPARENT)


# load and scale textures
def load_images(s):
    def load(name):
        path = os.path.join(TEXTURE_DIR, name)
        img = Image.open(path).convert("RGBA")
        w, h = img.size
        img = img.resize((int(w * s), int(h * s)), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    idle = load("smack_none.png")
    left = load("smack_left.png")
    right = load("smack_right.png")
    both = load("smack_both.png")
    frames = [left, right, left, right, both]   # random hit frames
    keep = [idle, left, right, both]            # prevent GC cleanup
    return idle, frames, keep


# initial images
img_idle, smack_frames, _keep = load_images(scale)

# main image widget
image_label = tk.Label(root, bg=TRANSPARENT, image=img_idle, bd=0, highlightthickness=0)
image_label.pack()

# counter + exit
counter_frame = tk.Frame(root, bg="white", bd=0, highlightthickness=0)
counter_frame.pack(fill="x", side="bottom")

counter_label = tk.Label(counter_frame, text="Smacks: 0", bg="white", fg="black",
                         bd=0, highlightthickness=0)
counter_label.pack(side="left")


def on_exit():
    kb.stop()
    ms.stop()
    root.destroy()


exit_btn = tk.Button(counter_frame, text="X", command=on_exit,
                     bg="white", fg="black", bd=0, highlightthickness=0)
exit_btn.pack(side="right")

# start position: bottom center
root.update_idletasks()
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
w, h = root.winfo_width(), root.winfo_height()
root.geometry(f"+{(sw - w) // 2}+{sh - h - 5}")

# dragging
drag_off = (0, 0)


def start_drag(e):
    global drag_off
    drag_off = (e.x_root - root.winfo_x(), e.y_root - root.winfo_y())


def do_drag(e):
    x = e.x_root - drag_off[0]
    y = e.y_root - drag_off[1]
    root.geometry(f"+{x}+{y}")


for wdg in (image_label, counter_frame):
    wdg.bind("<Button-1>", start_drag)
    wdg.bind("<B1-Motion>", do_drag)


# rescale images
def reload_scaled():
    global img_idle, smack_frames, _keep
    img_idle, smack_frames, _keep = load_images(scale)
    image_label.config(image=img_idle)


# mouse-wheel scaling
def on_scroll(e):
    global scale
    step = 0.05 if e.delta > 0 else -0.05
    ns = max(0.2, min(1.5, scale + step))
    if abs(ns - scale) < 1e-6:
        return
    scale = ns
    reload_scaled()
    root.update_idletasks()


image_label.bind("<MouseWheel>", on_scroll)


# main GUI loop
def gui_loop():
    global pending
    counter_label.config(text=f"Smacks: {hits}")
    if pending:
        pending = False
        frame = random.choice(smack_frames)
        image_label.config(image=frame)
        root.after(HIT_MS, lambda: image_label.config(image=img_idle))
    root.after(LOOP_MS, gui_loop)


gui_loop()
root.mainloop()
