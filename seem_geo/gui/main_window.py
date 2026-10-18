"""
SEEM Geo - Professional Desktop GUI
Tkinter-based desktop application wrapping the full ERT + MASW + Correlations
+ Fence + PDF Report pipeline. Runs on Windows, Mac, Linux with Python 3.8+.
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from seem_geo.core.project import SeemProject


class SeemGeoApp:
    """Main Tkinter window for SEEM Geo."""

    def __init__(self, root):
        self.root = root
        self.root.title("SEEM Geo - Professional ERT & MASW Processing Suite v1.1.0")
        self.root.geometry("900x650")
        self.project = None
        self.project_file = tk.StringVar(value="(none loaded)")
        self._build_ui()

    def _build_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Project...", command=self.new_project)
        file_menu.add_command(label="Open Project...", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Top project bar
        top_frame = ttk.Frame(self.root, padding=8)
        top_frame.pack(fill=tk.X)
        ttk.Label(top_frame, text="Project:").pack(side=tk.LEFT)
        ttk.Label(top_frame, textvariable=self.project_file,
                  foreground='blue').pack(side=tk.LEFT, padx=6)

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self._build_pipeline_tab()
        self._build_results_tab()
        self._build_log_tab()

        # Status bar
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN,
                  anchor=tk.W, padding=4).pack(fill=tk.X, side=tk.BOTTOM)

    def _build_pipeline_tab(self):
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text="Pipeline")
        ttk.Label(frame, text="SEEM Geo Processing Pipeline",
                  font=('Arial', 14, 'bold')).grid(row=0, column=0,
                                                   columnspan=2, pady=10, sticky='w')
        steps = [
            ("1. Generate synthetic data", self.run_gen_data),
            ("2. Run ERT batch inversion", self.run_ert),
            ("3. Run MASW batch processing", self.run_masw),
            ("4. Build correlation framework", self.run_corr),
            ("5. Build fence diagrams", self.run_fence),
            ("6. Build Vs30 map + bar chart", self.run_vs30),
            ("7. Export Google Earth KMZ", self.run_kmz),
            ("8. Build PDF report", self.run_report),
        ]
        for i, (label, cmd) in enumerate(steps):
            ttk.Button(frame, text=label, command=cmd, width=38).grid(
                row=i + 1, column=0, pady=4, sticky='w')
        ttk.Separator(frame, orient='horizontal').grid(row=len(steps) + 1,
                                                       column=0, columnspan=2,
                                                       sticky='ew', pady=10)
        ttk.Button(frame, text="RUN FULL PIPELINE", command=self.run_full_pipeline,
                   width=38).grid(row=len(steps) + 2, column=0, pady=4, sticky='w')

        # Progress
        self.progress = ttk.Progressbar(frame, mode='determinate', length=350)
        self.progress.grid(row=len(steps) + 3, column=0, pady=8, sticky='w')

    def _build_results_tab(self):
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text="Results")
        self.results_text = scrolledtext.ScrolledText(frame, height=28,
                                                      font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)

    def _build_log_tab(self):
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text="Log")
        self.log_text = scrolledtext.ScrolledText(frame, height=28,
                                                  font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ---- helpers ----
    def _log(self, msg):
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _result(self, msg):
        self.results_text.insert(tk.END, msg + '\n')
        self.results_text.see(tk.END)

    def _require_project(self):
        if self.project is None:
            messagebox.showwarning("No project", "Open or create a project first.")
            return False
        return True

    # ---- menu actions ----
    def new_project(self):
        d = filedialog.askdirectory(title="Choose empty directory for new project")
        if not d:
            return
        proj = SeemProject.init_default(d, name=os.path.basename(d))
        self.project = proj
        self.project_file.set(proj.file)
        self._log(f"[+] Created project: {proj.file}")

    def open_project(self):
        f = filedialog.askopenfilename(title="Open .seemproj file",
                                       filetypes=[("SEEM Project", "*.seemproj"),
                                                  ("JSON", "*.json"),
                                                  ("All", "*.*")])
        if not f:
            return
        self.project = SeemProject.load(f)
        self.project_file.set(f)
        self._log(f"[+] Loaded project: {f}")
        s = self.project.summary()
        self._result(f"Project: {s['name']}  |  {s['n_sites']} sites  |  Groups: {', '.join(s['groups'])}")

    def show_about(self):
        messagebox.showinfo("About SEEM Geo",
                            "SEEM Geo v1.1.0\n\n"
                            "Professional ERT & MASW Processing Suite\n"
                            "Open source - MIT License\n\n"
                            "For engineering-geology site investigations.")

    # ---- pipeline steps ----
    def _run_async(self, fn, name):
        if not self._require_project():
            return

        def worker():
            self.status.set(f"Running: {name}...")
            self.progress.start(10)
            try:
                fn(self.project)
                self._log(f"[+] {name} complete.")
            except Exception as e:
                self._log(f"[!] {name} failed: {e}")
                messagebox.showerror(name, str(e))
            finally:
                self.progress.stop()
                self.status.set("Ready.")
        threading.Thread(target=worker, daemon=True).start()

    def run_gen_data(self):
        from seem_geo.data.realistic_field_generator import generate_project_data
        self._run_async(lambda p: generate_project_data(p), "Generate data")

    def run_ert(self):
        from seem_geo.core.ert import batch_ert
        def fn(p):
            os.makedirs(p.ert_output_dir, exist_ok=True)
            r = batch_ert(p)
            self._result(f"ERT: {len(r)} stations processed.")
        self._run_async(fn, "ERT batch")

    def run_masw(self):
        from seem_geo.core.masw import batch_masw
        def fn(p):
            os.makedirs(p.masw_output_dir, exist_ok=True)
            r = batch_masw(p)
            self._result(f"MASW: {len(r)} stations processed.")
        self._run_async(fn, "MASW batch")

    def run_corr(self):
        from seem_geo.core.correlations import build_correlations
        def fn(p):
            s = build_correlations(p)
            for k, v in s.items():
                self._result(f"{k}: R^2={v['r2']:.3f} p={v['p']:.2e} n={v['n']}")
        self._run_async(fn, "Correlations")

    def run_fence(self):
        from seem_geo.core.fence import build_fence_diagrams
        self._run_async(lambda p: build_fence_diagrams(p), "Fence diagrams")

    def run_vs30(self):
        from seem_geo.reports.vs30_map import build_vs30_bar_chart
        self._run_async(lambda p: build_vs30_bar_chart(p), "Vs30 outputs")

    def run_kmz(self):
        from seem_geo.io.kmz_exporter import export_results_kmz
        self._run_async(lambda p: export_results_kmz(p), "KMZ export")

    def run_report(self):
        from seem_geo.reports.pdf_report import build_pdf_report
        self._run_async(lambda p: build_pdf_report(p), "PDF report")

    def run_full_pipeline(self):
        if not self._require_project():
            return
        for fn in (self.run_gen_data, self.run_ert, self.run_masw,
                   self.run_corr, self.run_fence, self.run_vs30,
                   self.run_kmz, self.run_report):
            fn()


def main():
    root = tk.Tk()
    app = SeemGeoApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
