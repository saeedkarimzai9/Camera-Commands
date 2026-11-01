import threading
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import pyvirtualcam

try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except Exception:
    PYNPUT_AVAILABLE = False


class CameraCommands:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Commands")
        self.root.geometry("440x570")
        self.root.minsize(400, 520)
        self.cap = None
        self.virtual_cam = None
        self.running = False
        self.worker = None
        self.frozen = False
        self.frozen_frame = None
        self.latest_frame = None
        self.lock = threading.Lock()
        self.mouse_listener = None
        self.camera_index = tk.IntVar(value=0)
        self.pixelate = tk.BooleanVar(value=False)
        self.invert = tk.BooleanVar(value=False)
        self.pixel_size = tk.IntVar(value=12)
        self.global_mouse = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Not running")
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="CAMERA COMMANDS", font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Live effects • Freeze • Frame stepping", foreground="#666").pack(anchor="w", pady=(0, 16))
        camera_row = ttk.Frame(outer)
        camera_row.pack(fill="x", pady=4)
        ttk.Label(camera_row, text="Camera device index").pack(side="left")
        ttk.Spinbox(camera_row, from_=0, to=20, width=6, textvariable=self.camera_index).pack(side="right")
        ttk.Separator(outer).pack(fill="x", pady=12)
        ttk.Label(outer, text="VIDEO EFFECTS", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Checkbutton(outer, text="Pixelate", variable=self.pixelate).pack(anchor="w", pady=3)
        ttk.Label(outer, text="Pixel block size").pack(anchor="w")
        ttk.Scale(outer, from_=2, to=40, variable=self.pixel_size, orient="horizontal").pack(fill="x")
        ttk.Checkbutton(outer, text="Invert colors", variable=self.invert).pack(anchor="w", pady=3)
        ttk.Separator(outer).pack(fill="x", pady=12)
        ttk.Label(outer, text="FRAME CONTROL", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=7)
        ttk.Button(buttons, text="Freeze", command=self.freeze).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(buttons, text="Unfreeze", command=self.unfreeze).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(buttons, text="Step 1 frame", command=self.step_frame).pack(side="left", expand=True, fill="x", padx=(4, 0))
        ttk.Separator(outer).pack(fill="x", pady=12)
        ttk.Checkbutton(outer, text="Enable global mouse controls (Left = freeze, Right = unfreeze)",
                        variable=self.global_mouse, command=self.toggle_mouse).pack(anchor="w", pady=3)
        if not PYNPUT_AVAILABLE:
            ttk.Label(outer, text="Install pynput to enable global mouse controls.", foreground="#a55").pack(anchor="w")
        ttk.Separator(outer).pack(fill="x", pady=12)
        ttk.Button(outer, text="Start camera", command=self.start).pack(fill="x", pady=4)
        ttk.Button(outer, text="Stop camera", command=self.stop).pack(fill="x", pady=4)
        ttk.Label(outer, textvariable=self.status, wraplength=390).pack(anchor="w", pady=(12, 4))
        ttk.Label(outer, text="Shortcuts: F = one frame • Space = toggle freeze • Esc = quit",
                  foreground="#666", wraplength=390).pack(anchor="w", pady=4)
        self.root.bind("<KeyPress-f>", lambda _e: self.step_frame())
        self.root.bind("<KeyPress-F>", lambda _e: self.step_frame())
        self.root.bind("<space>", lambda _e: self.toggle_freeze())
        self.root.bind("<Escape>", lambda _e: self.close())

    def start(self):
        if self.running:
            return
        index = self.camera_index.get()
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            messagebox.showerror("Camera unavailable", f"Could not open camera index {index}. Try another index.")
            return
        ok, frame = cap.read()
        if not ok:
            cap.release()
            messagebox.showerror("Camera error", "The camera opened but did not return a frame.")
            return
        height, width = frame.shape[:2]
        try:
            virtual_cam = pyvirtualcam.Camera(width=width, height=height, fps=30, print_fps=False)
        except Exception as exc:
            cap.release()
            messagebox.showerror("Virtual camera unavailable",
                                 "Could not connect to a virtual camera.\n\nStart OBS Virtual Camera, then try again.\n\n"
                                 f"Details: {exc}")
            return
        self.cap = cap
        self.virtual_cam = virtual_cam
        self.running = True
        self.frozen = False
        self.frozen_frame = None
        self.status.set(f"Running: camera {index} → {virtual_cam.device}")
        self.worker = threading.Thread(target=self._video_loop, daemon=True)
        self.worker.start()

    def _process(self, frame):
        output = frame.copy()
        if self.pixelate.get():
            h, w = output.shape[:2]
            block = max(2, int(self.pixel_size.get()))
            small_w = max(1, w // block)
            small_h = max(1, h // block)
            output = cv2.resize(output, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            output = cv2.resize(output, (w, h), interpolation=cv2.INTER_NEAREST)
        if self.invert.get():
            output = cv2.bitwise_not(output)
        return output

    def _video_loop(self):
        while self.running:
            if self.frozen:
                with self.lock:
                    frame = None if self.frozen_frame is None else self.frozen_frame.copy()
                if frame is not None:
                    self.virtual_cam.send(cv2.cvtColor(self._process(frame), cv2.COLOR_BGR2RGB))
                    self.virtual_cam.sleep_until_next_frame()
                else:
                    threading.Event().wait(0.01)
                continue
            ok, frame = self.cap.read()
            if not ok:
                threading.Event().wait(0.01)
                continue
            with self.lock:
                self.latest_frame = frame.copy()
            processed = self._process(frame)
            self.virtual_cam.send(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
            self.virtual_cam.sleep_until_next_frame()

    def freeze(self):
        with self.lock:
            source = self.latest_frame
            if source is not None:
                self.frozen_frame = source.copy()
                self.frozen = True
        self.status.set("Frozen. Press F or Step 1 frame to advance one frame.")

    def unfreeze(self):
        self.frozen = False
        self.status.set("Live video resumed." if self.running else "Not running")

    def step_frame(self):
        if not self.running or not self.frozen:
            self.status.set("Start the camera and freeze it before stepping frames.")
            return
        ok, frame = self.cap.read()
        if ok:
            with self.lock:
                self.frozen_frame = frame.copy()
                self.latest_frame = frame.copy()
            self.status.set("Advanced exactly one frame. Still frozen.")

    def toggle_freeze(self):
        self.unfreeze() if self.frozen else self.freeze()

    def toggle_mouse(self):
        if not PYNPUT_AVAILABLE:
            self.global_mouse.set(False)
            return
        if self.global_mouse.get():
            if self.mouse_listener is None:
                self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
                self.mouse_listener.start()
            self.status.set("Global mouse controls on: left freezes, right resumes.")
        else:
            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None
            self.status.set("Global mouse controls off.")

    def _on_mouse_click(self, x, y, button, pressed):
        if not pressed:
            return
        if button == mouse.Button.left:
            self.root.after(0, self.freeze)
        elif button == mouse.Button.right:
            self.root.after(0, self.unfreeze)

    def stop(self):
        self.running = False
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=1.0)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.virtual_cam is not None:
            self.virtual_cam.close()
            self.virtual_cam = None
        self.frozen = False
        self.status.set("Stopped")

    def close(self):
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
            self.mouse_listener = None
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CameraCommands(root)
    root.mainloop()
