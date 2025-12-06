import json
import logging
import os
import random
import sys
from typing import List, Tuple

from PIL import Image, ImageTk
import tkinter as tk
from pynput import keyboard, mouse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Bongobuddy:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.base_dir = self.get_base_dir()
        self.texture_dir = os.path.join(self.base_dir, self.config["texture_dir"])

        # Runtime state
        self.pending = False
        self.hits = 0
        self.scale = self.config["scale"]

        # Listeners
        self.kb_listener = keyboard.Listener(on_press=self.on_any_input)
        self.ms_listener = mouse.Listener(on_click=self.on_any_input)

        # GUI elements
        self.root = None
        self.image_label = None
        self.counter_label = None
        self.img_idle = None
        self.smack_frames: List[ImageTk.PhotoImage] = []
        self.keep: List[ImageTk.PhotoImage] = []

        self.setup_gui()
        self.load_images()

    def load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load config from {config_path}: {e}")
            # Fallback to defaults
            return {
                "hit_ms": 120,
                "loop_ms": 20,
                "scale": 0.4,
                "transparent_color": "magenta",
                "texture_dir": "Textures",
                "idle_image": "smack_none.png",
                "left_image": "smack_left.png",
                "right_image": "smack_right.png",
                "both_image": "smack_both.png"
            }

    def get_base_dir(self) -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def on_any_input(self, *_):
        self.hits += 1
        self.pending = True

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg=self.config["transparent_color"])
        self.root.attributes("-transparentcolor", self.config["transparent_color"])

        # Main image widget
        self.image_label = tk.Label(self.root, bg=self.config["transparent_color"], bd=0, highlightthickness=0)
        self.image_label.pack()

        # Counter and exit frame
        counter_frame = tk.Frame(self.root, bg="white", bd=0, highlightthickness=0)
        counter_frame.pack(fill="x", side="bottom")

        self.counter_label = tk.Label(counter_frame, text="Smacks: 0", bg="white", fg="black",
                                      bd=0, highlightthickness=0)
        self.counter_label.pack(side="left")

        exit_btn = tk.Button(counter_frame, text="X", command=self.on_exit,
                             bg="white", fg="black", bd=0, highlightthickness=0)
        exit_btn.pack(side="right")

        # Position window at bottom center
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        self.root.geometry(f"+{(sw - w) // 2}+{sh - h - 5}")

        # Dragging
        self.drag_off = (0, 0)

        def start_drag(e):
            self.drag_off = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

        def do_drag(e):
            x = e.x_root - self.drag_off[0]
            y = e.y_root - self.drag_off[1]
            self.root.geometry(f"+{x}+{y}")

        for wdg in (self.image_label, counter_frame):
            wdg.bind("<Button-1>", start_drag)
            wdg.bind("<B1-Motion>", do_drag)

        # Mouse wheel scaling
        self.image_label.bind("<MouseWheel>", self.on_scroll)

    def load_images(self):
        try:
            def load(name: str) -> ImageTk.PhotoImage:
                path = os.path.join(self.texture_dir, name)
                img = Image.open(path).convert("RGBA")
                w, h = img.size
                img = img.resize((int(w * self.scale), int(h * self.scale)), Image.LANCZOS)
                return ImageTk.PhotoImage(img)

            self.img_idle = load(self.config["idle_image"])
            left = load(self.config["left_image"])
            right = load(self.config["right_image"])
            both = load(self.config["both_image"])
            self.smack_frames = [left, right, left, right, both]
            self.keep = [self.img_idle, left, right, both]
            self.image_label.config(image=self.img_idle)
        except Exception as e:
            logging.error(f"Failed to load images: {e}")
            self.root.destroy()
            raise

    def reload_scaled(self):
        try:
            self.load_images()
        except Exception as e:
            logging.error(f"Failed to reload scaled images: {e}")

    def on_scroll(self, e):
        step = 0.05 if e.delta > 0 else -0.05
        ns = max(0.2, min(1.5, self.scale + step))
        if abs(ns - self.scale) < 1e-6:
            return
        self.scale = ns
        self.reload_scaled()
        self.root.update_idletasks()

    def on_exit(self):
        self.kb_listener.stop()
        self.ms_listener.stop()
        self.root.destroy()

    def gui_loop(self):
        self.counter_label.config(text=f"Smacks: {self.hits}")
        if self.pending:
            self.pending = False
            frame = random.choice(self.smack_frames)
            self.image_label.config(image=frame)
            self.root.after(self.config["hit_ms"], lambda: self.image_label.config(image=self.img_idle))
        self.root.after(self.config["loop_ms"], self.gui_loop)

    def run(self):
        self.kb_listener.start()
        self.ms_listener.start()
        self.gui_loop()
        self.root.mainloop()


if __name__ == "__main__":
    app = Bongobuddy()
    app.run()
