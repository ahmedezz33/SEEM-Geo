"""
Interactive Dispersion Picker - Tkinter + Matplotlib GUI
Click on the f-v image to manually pick/edit the fundamental-mode Rayleigh
dispersion curve. Supports left-click to add, right-click to remove,
save to CSV and recompute Vs profile.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class DispersionPicker:
    """Interactive dispersion-curve picker."""

    def __init__(self, root, csv_path):
        self.root = root
        self.csv_path = csv_path
        self.root.title(f"SEEM Geo - Dispersion Picker - {os.path.basename(csv_path)}")
        self.root.geometry("1050x780")

        from seem_geo.core.masw import read_shot_csv, slant_stack_fv, auto_pick_dispersion
        t, x, traces = read_shot_csv(csv_path)
        self.f_axis, self.v_axis, self.FV = slant_stack_fv(traces, t, x)
        auto_picks = auto_pick_dispersion(self.f_axis, self.v_axis, self.FV)
        self.picks = list(map(tuple, auto_picks)) if len(auto_picks) else []

        self._build_ui()
        self._redraw()

    def _build_ui(self):
        tbar = ttk.Frame(self.root, padding=6)
        tbar.pack(fill=tk.X)
        ttk.Button(tbar, text="Clear picks", command=self._clear).pack(side=tk.LEFT, padx=4)
        ttk.Button(tbar, text="Auto-pick", command=self._auto_pick).pack(side=tk.LEFT, padx=4)
        ttk.Button(tbar, text="Save CSV", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Label(tbar, text="  (Left click: add  |  Right click: remove)",
                  foreground='grey').pack(side=tk.LEFT, padx=12)

        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(self.canvas, self.root)
        self.canvas.mpl_connect('button_press_event', self._on_click)

    def _redraw(self):
        self.ax.clear()
        F, V = np.meshgrid(self.f_axis, self.v_axis, indexing='ij')
        self.ax.pcolormesh(F, V, self.FV, cmap='jet', shading='auto', vmin=0, vmax=1)
        if self.picks:
            arr = np.array(self.picks)
            self.ax.plot(arr[:, 0], arr[:, 1], 'wo-', markersize=8,
                         markeredgecolor='black', linewidth=1.5)
        self.ax.set_xlabel('Frequency (Hz)', fontsize=11)
        self.ax.set_ylabel('Phase velocity (m/s)', fontsize=11)
        self.ax.set_title(f'Dispersion picker - {len(self.picks)} picks', fontweight='bold')
        self.canvas.draw()

    def _on_click(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == 1:  # left: add
            self.picks.append((event.xdata, event.ydata))
            self.picks.sort(key=lambda p: p[0])
        elif event.button == 3 and self.picks:  # right: remove nearest
            arr = np.array(self.picks)
            d = (arr[:, 0] - event.xdata) ** 2 + ((arr[:, 1] - event.ydata) / 10) ** 2
            idx = int(np.argmin(d))
            self.picks.pop(idx)
        self._redraw()

    def _clear(self):
        self.picks = []
        self._redraw()

    def _auto_pick(self):
        from seem_geo.core.masw import auto_pick_dispersion
        p = auto_pick_dispersion(self.f_axis, self.v_axis, self.FV)
        self.picks = list(map(tuple, p)) if len(p) else []
        self._redraw()

    def _save(self):
        if not self.picks:
            messagebox.showinfo("No picks", "Nothing to save.")
            return
        out = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV', '*.csv')],
            initialfile=os.path.splitext(os.path.basename(self.csv_path))[0] + '_picks.csv')
        if not out:
            return
        pd.DataFrame(self.picks, columns=['freq_hz', 'phase_vel_ms']).to_csv(out, index=False)
        messagebox.showinfo("Saved", f"Saved {len(self.picks)} picks to:\n{out}")


def launch_picker(csv_path):
    root = tk.Tk()
    DispersionPicker(root, csv_path)
    root.mainloop()
