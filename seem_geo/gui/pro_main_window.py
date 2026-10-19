"""
SEEM Geo - Professional Desktop GUI (v4)
=========================================
Enhancements over v3:
- Settings menu: Image Output dialog (DPI, size, colors, format)
- Auto-apply user settings at startup from ~/.seem_geo_settings.json
Features from v3:
- Mode selector: ERT only / MASW only / Both
- Dashboard split in 3 columns (ERT | MASW | Shared)
- New-project wizard: template / empty / import stations CSV
- Side-by-side Viewer: show pseudosection + inverted together
"""
import os
import sys
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from seem_geo.core.project import SeemProject

# Apply user image-output settings (DPI, figsize, colormap) at startup.
# Importing this module reads ~/.seem_geo_settings.json and patches matplotlib.
try:
    from seem_geo import settings as _seem_settings
except ImportError:
    _seem_settings = None


# ======================================================================
# Themes
# ======================================================================
THEMES = {
    'light': {'bg': '#F5F5F5', 'panel': '#FFFFFF', 'fg': '#1F2937',
              'muted': '#6B7280', 'accent': '#1F4E79', 'accent_fg': '#FFFFFF',
              'success': '#10B981', 'warning': '#F59E0B', 'error': '#EF4444',
              'queued': '#9CA3AF', 'border': '#E5E7EB',
              'ert_color': '#DC2626', 'masw_color': '#2563EB', 'shared_color': '#7C3AED',
              'log_bg': '#1F2937', 'log_fg': '#F3F4F6'},
    'dark':  {'bg': '#0F172A', 'panel': '#1E293B', 'fg': '#F1F5F9',
              'muted': '#94A3B8', 'accent': '#3B82F6', 'accent_fg': '#FFFFFF',
              'success': '#10B981', 'warning': '#F59E0B', 'error': '#EF4444',
              'queued': '#64748B', 'border': '#334155',
              'ert_color': '#F87171', 'masw_color': '#60A5FA', 'shared_color': '#A78BFA',
              'log_bg': '#020617', 'log_fg': '#E2E8F0'},
}


# Pipeline step groups
ERT_STEPS = [
    ('⚡', 'ERT inversion',          'ert'),
    ('📊', 'ERT fence diagram',       'ert_fence'),
]
MASW_STEPS = [
    ('🌊', 'MASW processing',         'masw'),
    ('📈', 'Vs30 bar chart',          'vs30'),
    ('📊', 'MASW fence diagram',      'masw_fence'),
]
SHARED_STEPS = [
    ('📥', 'Generate data',           'gen_data'),
    ('🔗', 'Correlations',            'corr'),
    ('🌍', 'Google Earth KMZ',        'kmz'),
    ('📄', 'PDF Report',              'pdf'),
]


class StepCard(tk.Frame):
    STATES = {
        'idle':    ('⚪', 'Idle',    'queued'),
        'running': ('⏳', 'Running', 'warning'),
        'done':    ('✅', 'Done',    'success'),
        'failed':  ('❌', 'Failed',  'error'),
        'skipped': ('⊘',  'Skipped', 'muted'),
    }

    def __init__(self, master, icon, label, key, theme, on_run, accent_color):
        super().__init__(master, bg=theme['panel'],
                         highlightthickness=1,
                         highlightbackground=theme['border'])
        self.theme = theme
        self.key = key
        self.on_run = on_run
        self.state = 'idle'
        self.accent_color = accent_color
        self._build(icon, label)

    def _build(self, icon, label):
        t = self.theme
        # Accent stripe on the left
        tk.Frame(self, bg=self.accent_color, width=4).pack(side=tk.LEFT, fill=tk.Y)

        inner = tk.Frame(self, bg=t['panel'])
        inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        row1 = tk.Frame(inner, bg=t['panel'])
        row1.pack(fill=tk.X, padx=10, pady=(8, 2))
        tk.Label(row1, text=icon, font=('Segoe UI Emoji', 16),
                 bg=t['panel']).pack(side=tk.LEFT)
        name_f = tk.Frame(row1, bg=t['panel'])
        name_f.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        tk.Label(name_f, text=label, font=('Segoe UI', 10, 'bold'),
                 bg=t['panel'], fg=t['fg']).pack(anchor='w')
        self.state_lbl = tk.Label(name_f, text='Idle',
                                   font=('Segoe UI', 8),
                                   bg=t['panel'], fg=t['queued'])
        self.state_lbl.pack(anchor='w')
        self.state_badge = tk.Label(row1, text='⚪', font=('Segoe UI Emoji', 12),
                                     bg=t['panel'], fg=t['queued'])
        self.state_badge.pack(side=tk.RIGHT)

        self.progress = ttk.Progressbar(inner, mode='indeterminate', length=100)
        self.progress.pack(fill=tk.X, padx=10, pady=2)

        row3 = tk.Frame(inner, bg=t['panel'])
        row3.pack(fill=tk.X, padx=10, pady=(2, 8))
        self.timing_lbl = tk.Label(row3, text='', font=('Segoe UI', 8),
                                    bg=t['panel'], fg=t['muted'])
        self.timing_lbl.pack(side=tk.LEFT)
        self.run_btn = tk.Button(row3, text='▶', font=('Segoe UI', 8, 'bold'),
                                  bg=self.accent_color, fg='white',
                                  relief='flat', padx=10, pady=1, cursor='hand2',
                                  command=lambda: self.on_run(self.key))
        self.run_btn.pack(side=tk.RIGHT)

    def set_state(self, state, timing=''):
        self.state = state
        icon, label, color_key = self.STATES[state]
        color = self.theme[color_key]
        self.state_badge.config(text=icon, fg=color)
        self.state_lbl.config(text=label, fg=color)
        if timing:
            self.timing_lbl.config(text=timing)
        if state == 'running':
            self.progress.start(10)
            self.run_btn.config(state='disabled')
        else:
            self.progress.stop()
            self.run_btn.config(state='normal' if state != 'skipped' else 'disabled')


# ======================================================================
# New-project wizard dialog
# ======================================================================
class NewProjectDialog(tk.Toplevel):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.title('New Project')
        self.geometry('520x420')
        self.theme = theme
        self.result = None
        self.transient(parent)
        self.grab_set()
        self.configure(bg=theme['bg'])
        self._build()

    def _build(self):
        t = self.theme
        tk.Label(self, text='🗂️  Create new project',
                 font=('Segoe UI', 14, 'bold'),
                 bg=t['bg'], fg=t['fg']).pack(pady=14)
        tk.Label(self, text='Choose a starting mode:',
                 font=('Segoe UI', 10),
                 bg=t['bg'], fg=t['muted']).pack(pady=(0, 10))

        self.mode = tk.StringVar(value='template')

        def mode_card(key, title, desc):
            card = tk.Frame(self, bg=t['panel'],
                            highlightthickness=1, highlightbackground=t['border'])
            card.pack(fill=tk.X, padx=20, pady=5)
            rb = tk.Radiobutton(card, text=title,
                                 variable=self.mode, value=key,
                                 font=('Segoe UI', 10, 'bold'),
                                 bg=t['panel'], fg=t['accent'],
                                 selectcolor=t['bg'], anchor='w')
            rb.pack(fill=tk.X, padx=10, pady=(8, 0))
            tk.Label(card, text=desc, font=('Segoe UI', 9),
                      bg=t['panel'], fg=t['muted'],
                      justify='left', wraplength=460).pack(fill=tk.X, padx=30, pady=(0, 8))

        mode_card('template',
                   '📋 Default template (12 sample sites)',
                   'Pre-filled project with 12 example sites (BH1-BH12) across 4 engineering groups. '
                   'Use for learning or quick tests. Replace with your own data later.')
        mode_card('empty',
                   '🆕 Empty project (0 sites)',
                   'Blank project — you add your own sites later via a stations.csv file. '
                   'Best when importing real field data.')
        mode_card('import',
                   '📥 Import stations from CSV',
                   'Load site list from a CSV file (columns: bh, group, chainage_km, UCS, RQD, N60).')

        # Name
        name_frame = tk.Frame(self, bg=t['bg'])
        name_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(name_frame, text='Project name:', font=('Segoe UI', 9),
                 bg=t['bg'], fg=t['fg']).pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value='My Project')
        tk.Entry(name_frame, textvariable=self.name_var,
                  font=('Segoe UI', 10), width=30).pack(side=tk.LEFT, padx=8)

        # Buttons
        btn_frame = tk.Frame(self, bg=t['bg'])
        btn_frame.pack(pady=16)
        tk.Button(btn_frame, text='Cancel', font=('Segoe UI', 10),
                   bg=t['panel'], fg=t['fg'], relief='flat', padx=14, pady=6,
                   command=self.destroy).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Create ▶', font=('Segoe UI', 10, 'bold'),
                   bg=t['accent'], fg=t['accent_fg'], relief='flat',
                   padx=14, pady=6, cursor='hand2',
                   command=self._on_create).pack(side=tk.LEFT, padx=5)

    def _on_create(self):
        self.result = {'mode': self.mode.get(), 'name': self.name_var.get()}
        self.destroy()


# ======================================================================
# Main window
# ======================================================================
class SeemGeoProApp:
    def __init__(self, root):
        self.root = root
        self.root.title('SEEM Geo Pro — v3')
        self.root.geometry('1400x850')
        self.root.minsize(1100, 700)

        self.theme_name = 'light'
        self.theme = THEMES[self.theme_name]
        self.project = None
        self.step_cards = {}
        self.run_mode = tk.StringVar(value='both')  # 'ert', 'masw', 'both'

        self._configure_style()
        self._build_menu()
        self._build_toolbar()
        self._build_main()
        self._build_statusbar()
        self._apply_theme()

    def _configure_style(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass

    def _apply_theme(self):
        t = self.theme
        self.root.configure(bg=t['bg'])
        self.style.configure('TNotebook', background=t['bg'], borderwidth=0)
        self.style.configure('TNotebook.Tab', background=t['panel'],
                             foreground=t['fg'], padding=[16, 8], borderwidth=0)
        self.style.map('TNotebook.Tab',
                       background=[('selected', t['accent'])],
                       foreground=[('selected', t['accent_fg'])])
        self.style.configure('Treeview', background=t['panel'],
                             fieldbackground=t['panel'], foreground=t['fg'],
                             borderwidth=0, rowheight=24)

    def _build_menu(self):
        m = tk.Menu(self.root); self.root.config(menu=m)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label='New Project...', command=self.new_project, accelerator='Ctrl+N')
        f.add_command(label='Open Project...', command=self.open_project, accelerator='Ctrl+O')
        f.add_separator()
        f.add_command(label='Import stations CSV', command=self.import_stations_csv)
        f.add_command(label='Open Outputs Folder', command=self.open_outputs_folder)
        f.add_separator()
        f.add_command(label='Exit', command=self.root.quit)
        m.add_cascade(label='File', menu=f)

        v = tk.Menu(m, tearoff=0)
        v.add_command(label='Toggle Dark / Light', command=self.toggle_theme)
        m.add_cascade(label='View', menu=v)

        # Settings menu
        settings_menu = tk.Menu(m, tearoff=0)
        settings_menu.add_command(label='⚙️  Image Output (DPI, size, colors)...',
                                    command=self.open_image_settings,
                                    accelerator='Ctrl+,')
        m.add_cascade(label='Settings', menu=settings_menu)
        self.root.bind('<Control-comma>', lambda e: self.open_image_settings())

        tools = tk.Menu(m, tearoff=0)
        tools.add_command(label='Convert SYSCAL Pro .bin', command=self.convert_syscal)
        tools.add_command(label='Dispersion Picker', command=self.launch_picker)
        m.add_cascade(label='Tools', menu=tools)

        h = tk.Menu(m, tearoff=0)
        h.add_command(label='Docs', command=lambda: self._open_url('https://ahmedezz33.github.io/SEEM-Geo'))
        h.add_command(label='GitHub', command=lambda: self._open_url('https://github.com/ahmedezz33/SEEM-Geo'))
        h.add_command(label='Cite (DOI)', command=lambda: self._open_url('https://doi.org/10.5281/zenodo.23455148'))
        h.add_separator()
        h.add_command(label='About', command=self.show_about)
        m.add_cascade(label='Help', menu=h)

        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_project())

    def _build_toolbar(self):
        t = self.theme
        self.toolbar = tk.Frame(self.root, bg=t['panel'], height=56,
                                 highlightthickness=0)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        self.toolbar.pack_propagate(False)

        def tool_btn(parent, text, cmd, color=None, primary=False):
            bg = color if color else (t['accent'] if primary else t['panel'])
            fg = 'white' if (primary or color) else t['fg']
            b = tk.Button(parent, text=text, font=('Segoe UI', 10),
                          bg=bg, fg=fg, relief='flat', padx=14, pady=8,
                          cursor='hand2', command=cmd)
            b.pack(side=tk.LEFT, padx=4, pady=10)
            return b

        tool_btn(self.toolbar, '📁 New', self.new_project)
        tool_btn(self.toolbar, '📂 Open', self.open_project)

        tk.Frame(self.toolbar, bg=t['border'], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=14)

        # Mode selector (ERT / MASW / Both)
        tk.Label(self.toolbar, text='Mode:', font=('Segoe UI', 10, 'bold'),
                 bg=t['panel'], fg=t['fg']).pack(side=tk.LEFT, padx=(8, 6))

        for val, label, color in [('ert', '⚡ ERT only', t['ert_color']),
                                     ('masw', '🌊 MASW only', t['masw_color']),
                                     ('both', '⚡+🌊 Both', t['shared_color'])]:
            tk.Radiobutton(self.toolbar, text=label, variable=self.run_mode,
                            value=val, font=('Segoe UI', 9),
                            bg=t['panel'], fg=t['fg'],
                            selectcolor=t['bg'], indicatoron=True,
                            cursor='hand2').pack(side=tk.LEFT, padx=4)

        tk.Frame(self.toolbar, bg=t['border'], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=14)

        self.run_btn = tool_btn(self.toolbar, '▶ Run Selected Mode',
                                 self.run_mode_pipeline, primary=True)

        tk.Frame(self.toolbar, bg=t['border'], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=14)
        tool_btn(self.toolbar, '🔬 Compare Inversions', self.compare_inversions)
        tool_btn(self.toolbar, '📊 Toggle QC in PDF', self.toggle_qc_pdf)
        tool_btn(self.toolbar, '🔧 Convert SYSCAL', self.convert_syscal)

        self.theme_btn = tool_btn(self.toolbar, '🌙 Dark', self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=10)

    def _build_main(self):
        t = self.theme
        main = tk.Frame(self.root, bg=t['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        # Sidebar
        self.sidebar = tk.Frame(main, bg=t['panel'], width=260,
                                 highlightthickness=1, highlightbackground=t['border'])
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        self.sidebar.pack_propagate(False)

        hdr = tk.Frame(self.sidebar, bg=t['panel'])
        hdr.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(hdr, text='📂 PROJECT', font=('Segoe UI', 9, 'bold'),
                 bg=t['panel'], fg=t['muted']).pack(anchor='w')
        self.project_name_lbl = tk.Label(hdr, text='(no project loaded)',
                                          font=('Segoe UI', 11, 'bold'),
                                          bg=t['panel'], fg=t['accent'],
                                          wraplength=220, justify='left')
        self.project_name_lbl.pack(anchor='w', pady=(4, 0))

        self.tree = ttk.Treeview(self.sidebar, show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Right side — tabs
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_dashboard_tab()
        self._build_results_tab()
        self._build_viewer_tab()
        self._build_log_tab()

    def _build_dashboard_tab(self):
        t = self.theme
        frame = tk.Frame(self.notebook, bg=t['bg'])
        self.notebook.add(frame, text='  📊 Dashboard  ')

        hdr = tk.Frame(frame, bg=t['bg'])
        hdr.pack(fill=tk.X, padx=20, pady=(16, 8))
        tk.Label(hdr, text='Pipeline Dashboard',
                 font=('Segoe UI', 15, 'bold'),
                 bg=t['bg'], fg=t['fg']).pack(side=tk.LEFT)
        tk.Label(hdr, text='   •   Use Mode selector above to choose ERT, MASW, or Both',
                 font=('Segoe UI', 9),
                 bg=t['bg'], fg=t['muted']).pack(side=tk.LEFT)

        # 3-column layout: ERT | MASW | Shared
        cols = tk.Frame(frame, bg=t['bg'])
        cols.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)
        for i in range(3):
            cols.grid_columnconfigure(i, weight=1, uniform='c')

        self._build_column(cols, 0, '⚡  ERT Workflow', t['ert_color'], ERT_STEPS)
        self._build_column(cols, 1, '🌊  MASW Workflow', t['masw_color'], MASW_STEPS)
        self._build_column(cols, 2, '🔗  Shared Steps', t['shared_color'], SHARED_STEPS)

    def _build_column(self, parent, col, title, color, steps):
        t = self.theme
        col_frame = tk.Frame(parent, bg=t['panel'],
                              highlightthickness=1, highlightbackground=t['border'])
        col_frame.grid(row=0, column=col, padx=8, pady=4, sticky='nsew')

        tk.Frame(col_frame, bg=color, height=4).pack(fill=tk.X)
        tk.Label(col_frame, text=title, font=('Segoe UI', 11, 'bold'),
                 bg=t['panel'], fg=color).pack(anchor='w', padx=12, pady=(10, 8))

        for icon, label, key in steps:
            card = StepCard(col_frame, icon, label, key, self.theme, self.run_step, color)
            card.pack(fill=tk.X, padx=10, pady=4)
            self.step_cards[key] = card

    def _build_results_tab(self):
        t = self.theme
        frame = tk.Frame(self.notebook, bg=t['bg'])
        self.notebook.add(frame, text='  📈 Results  ')
        self.results_text = scrolledtext.ScrolledText(
            frame, font=('Consolas', 10), bg=t['panel'], fg=t['fg'],
            insertbackground=t['fg'], relief='flat', padx=14, pady=14)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        self.results_text.tag_config('header', font=('Segoe UI', 12, 'bold'), foreground=t['accent'])
        self.results_text.tag_config('success', foreground=t['success'])
        self.results_text.tag_config('warning', foreground=t['warning'])
        self.results_text.tag_config('ert', foreground=t['ert_color'])
        self.results_text.tag_config('masw', foreground=t['masw_color'])
        self.results_text.tag_config('muted', foreground=t['muted'])

    def _build_viewer_tab(self):
        t = self.theme
        frame = tk.Frame(self.notebook, bg=t['bg'])
        self.notebook.add(frame, text='  🖼️ Viewer  ')

        tbar = tk.Frame(frame, bg=t['panel'], height=44)
        tbar.pack(fill=tk.X); tbar.pack_propagate(False)

        tk.Label(tbar, text='View mode:', font=('Segoe UI', 10, 'bold'),
                 bg=t['panel'], fg=t['fg']).pack(side=tk.LEFT, padx=10)

        self.view_mode = tk.StringVar(value='single')
        tk.Radiobutton(tbar, text='Single image', variable=self.view_mode,
                        value='single', bg=t['panel'], fg=t['fg'],
                        font=('Segoe UI', 9), cursor='hand2',
                        command=self._refresh_viewer).pack(side=tk.LEFT, padx=4)
        tk.Radiobutton(tbar, text='Compare ERT (pseudo + inverted)',
                        variable=self.view_mode, value='ert_compare',
                        bg=t['panel'], fg=t['fg'], font=('Segoe UI', 9),
                        cursor='hand2', command=self._refresh_viewer).pack(side=tk.LEFT, padx=4)
        tk.Radiobutton(tbar, text='Compare MASW (dispersion + Vs)',
                        variable=self.view_mode, value='masw_compare',
                        bg=t['panel'], fg=t['fg'], font=('Segoe UI', 9),
                        cursor='hand2', command=self._refresh_viewer).pack(side=tk.LEFT, padx=4)

        tk.Frame(tbar, bg=t['border'], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=8)

        tk.Label(tbar, text='Select:', font=('Segoe UI', 10),
                 bg=t['panel'], fg=t['fg']).pack(side=tk.LEFT, padx=4)
        self.image_var = tk.StringVar()
        self.image_dropdown = ttk.Combobox(tbar, textvariable=self.image_var,
                                            state='readonly', width=50)
        self.image_dropdown.pack(side=tk.LEFT, padx=4)
        self.image_dropdown.bind('<<ComboboxSelected>>', self._on_image_selected)
        tk.Button(tbar, text='🔄', bg=t['panel'], fg=t['fg'],
                   font=('Segoe UI', 9), relief='flat', cursor='hand2',
                   command=self._refresh_image_list).pack(side=tk.LEFT, padx=4)

        # Matplotlib canvas
        self.viewer_fig = Figure(figsize=(12, 7), facecolor=t['panel'])
        self.viewer_fig.text(0.5, 0.5,
                              'Open a project and run steps\nto preview results here.',
                              ha='center', va='center', fontsize=12, color=t['muted'])
        self.viewer_canvas = FigureCanvasTkAgg(self.viewer_fig, master=frame)
        self.viewer_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_log_tab(self):
        t = self.theme
        frame = tk.Frame(self.notebook, bg=t['bg'])
        self.notebook.add(frame, text='  📝 Log  ')
        self.log_text = scrolledtext.ScrolledText(
            frame, font=('Consolas', 9), bg=t['log_bg'], fg=t['log_fg'],
            insertbackground=t['log_fg'], relief='flat', padx=14, pady=14)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        self.log_text.tag_config('info', foreground='#60A5FA')
        self.log_text.tag_config('success', foreground='#34D399')
        self.log_text.tag_config('warning', foreground='#FBBF24')
        self.log_text.tag_config('error', foreground='#F87171')
        self.log_text.tag_config('time', foreground='#9CA3AF')
        self.log_text.tag_config('ert', foreground='#F87171')
        self.log_text.tag_config('masw', foreground='#60A5FA')

    def _build_statusbar(self):
        t = self.theme
        bar = tk.Frame(self.root, bg=t['panel'], height=28,
                       highlightthickness=1, highlightbackground=t['border'])
        bar.pack(fill=tk.X, side=tk.BOTTOM); bar.pack_propagate(False)
        self.status_lbl = tk.Label(bar, text='Ready.', font=('Segoe UI', 9),
                                     bg=t['panel'], fg=t['fg'])
        self.status_lbl.pack(side=tk.LEFT, padx=12)
        tk.Frame(bar, bg=t['border'], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=4)
        self.project_info_lbl = tk.Label(bar, text='No project loaded',
                                           font=('Segoe UI', 9),
                                           bg=t['panel'], fg=t['muted'])
        self.project_info_lbl.pack(side=tk.LEFT, padx=4)
        tk.Label(bar, text='SEEM Geo v1.2.1', font=('Segoe UI', 9),
                  bg=t['panel'], fg=t['muted']).pack(side=tk.RIGHT, padx=12)

    def toggle_theme(self):
        self.theme_name = 'dark' if self.theme_name == 'light' else 'light'
        self.theme = THEMES[self.theme_name]
        for w in list(self.root.winfo_children()):
            if isinstance(w, (tk.Frame, ttk.Notebook)):
                w.destroy()
        self._configure_style()
        self._build_toolbar()
        self._build_main()
        self._build_statusbar()
        self._apply_theme()
        if self.project:
            self._refresh_project_tree()

    def _log(self, msg, level='info'):
        ts = time.strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f'[{ts}] ', 'time')
        self.log_text.insert(tk.END, msg + '\n', level)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _result(self, msg, tag=None):
        self.results_text.insert(tk.END, msg + '\n', tag) if tag \
            else self.results_text.insert(tk.END, msg + '\n')
        self.results_text.see(tk.END)

    def _status(self, msg):
        self.status_lbl.config(text=msg)

    # ---------- project ops ----------
    def new_project(self):
        dlg = NewProjectDialog(self.root, self.theme)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        d = filedialog.askdirectory(title='Choose empty folder for the new project')
        if not d:
            return
        mode = dlg.result['mode']
        name = dlg.result['name']
        try:
            if mode == 'template':
                self.project = SeemProject.init_default(d, name=name)
                self._log(f'Created template project: {name} (12 sample sites)', 'success')
            elif mode == 'empty':
                self._create_empty_project(d, name)
                self._log(f'Created empty project: {name} (0 sites — add your own)', 'success')
            elif mode == 'import':
                csv_file = filedialog.askopenfilename(
                    title='Choose stations CSV',
                    filetypes=[('CSV', '*.csv')])
                if not csv_file:
                    return
                self._create_project_from_csv(d, name, csv_file)
                self._log(f'Created project from CSV: {csv_file}', 'success')
            self._on_project_loaded()
        except Exception as e:
            messagebox.showerror('New Project', str(e))
            self._log(f'Error creating project: {e}', 'error')

    def _create_empty_project(self, project_dir, name):
        """Create a project with 0 sites — user adds them later."""
        os.makedirs(project_dir, exist_ok=True)
        from copy import deepcopy
        from seem_geo.core.project import DEFAULT_CONFIG
        cfg = deepcopy(DEFAULT_CONFIG)
        cfg['project']['name'] = name
        cfg['sites'] = []  # 0 sites
        project_file = os.path.join(project_dir, 'project.seemproj')
        with open(project_file, 'w') as f:
            json.dump(cfg, f, indent=2)
        self.project = SeemProject(config=cfg, project_file=project_file)
        self.project._make_dirs()

    def _create_project_from_csv(self, project_dir, name, csv_file):
        """Create project with sites loaded from CSV."""
        import csv as csvmod
        from copy import deepcopy
        from seem_geo.core.project import DEFAULT_CONFIG
        os.makedirs(project_dir, exist_ok=True)
        cfg = deepcopy(DEFAULT_CONFIG)
        cfg['project']['name'] = name
        cfg['sites'] = []
        with open(csv_file) as f:
            reader = csvmod.DictReader(f)
            for row in reader:
                site = {
                    'bh': row.get('bh', row.get('BH', '')),
                    'ert_id': row.get('ert_id', f"ERT-{len(cfg['sites'])+1:02d}"),
                    'masw_id': row.get('masw_id', f"MW-{len(cfg['sites'])+1:02d}"),
                    'group': row.get('group', row.get('Group', 'G1')),
                    'chainage_km': float(row.get('chainage_km', 0)),
                    'ucs_mpa': float(row.get('ucs_mpa', row.get('UCS', 10))),
                    'rqd_pct': float(row.get('rqd_pct', row.get('RQD', 50))),
                    'n60': float(row.get('n60', row.get('N60', 30))),
                }
                cfg['sites'].append(site)
        project_file = os.path.join(project_dir, 'project.seemproj')
        with open(project_file, 'w') as f:
            json.dump(cfg, f, indent=2)
        self.project = SeemProject(config=cfg, project_file=project_file)
        self.project._make_dirs()

    def open_project(self):
        f = filedialog.askopenfilename(
            title='Open .seemproj file',
            filetypes=[('SEEM Project', '*.seemproj'), ('All', '*.*')])
        if not f:
            return
        try:
            self.project = SeemProject.load(f)
            self._on_project_loaded()
            self._log(f'Loaded: {f}', 'success')
        except Exception as e:
            messagebox.showerror('Open Project', str(e))

    def import_stations_csv(self):
        if not self._require_project():
            return
        csv_file = filedialog.askopenfilename(
            title='Choose stations CSV (bh, group, chainage_km, ucs_mpa, rqd_pct, n60)',
            filetypes=[('CSV', '*.csv')])
        if not csv_file:
            return
        import csv as csvmod
        with open(csv_file) as f:
            reader = csvmod.DictReader(f)
            new_sites = []
            for row in reader:
                new_sites.append({
                    'bh': row.get('bh', ''),
                    'ert_id': row.get('ert_id', f"ERT-{len(new_sites)+1:02d}"),
                    'masw_id': row.get('masw_id', f"MW-{len(new_sites)+1:02d}"),
                    'group': row.get('group', 'G1'),
                    'chainage_km': float(row.get('chainage_km', 0)),
                    'ucs_mpa': float(row.get('ucs_mpa', 10)),
                    'rqd_pct': float(row.get('rqd_pct', 50)),
                    'n60': float(row.get('n60', 30)),
                })
        self.project.config['sites'] = new_sites
        self.project.save()
        self._on_project_loaded()
        self._log(f'Imported {len(new_sites)} sites from CSV', 'success')

    def _on_project_loaded(self):
        s = self.project.summary()
        self.project_name_lbl.config(text=s['name'])
        self.project_info_lbl.config(text=f"📁 {s['name']}   •   {s['n_sites']} sites")
        self._status(f"Opened: {s['name']}")
        self._refresh_project_tree()
        self._refresh_image_list()
        self._result(f"\n{'=' * 50}", 'muted')
        self._result(f"Project: {s['name']}", 'header')
        self._result(f"  Sites: {s['n_sites']}")
        if s['n_sites'] == 0:
            self._result('  ⚠ Empty project — add sites via File → Import stations CSV', 'warning')
        self._result(f"  Root:  {s['root']}", 'muted')
        for card in self.step_cards.values():
            card.set_state('idle')

    def _refresh_project_tree(self):
        self.tree.delete(*self.tree.get_children())
        if not self.project:
            return
        s = self.project.summary()
        root = self.tree.insert('', 'end', text=f"📁 {s['name']}", open=True)
        sites_node = self.tree.insert(root, 'end',
                                       text=f"📍 Sites ({s['n_sites']})",
                                       open=(s['n_sites'] <= 15))
        for site in self.project.sites:
            self.tree.insert(sites_node, 'end',
                             text=f"🔵 {site['bh']} ({site['group']})")
        grp_node = self.tree.insert(root, 'end', text=f"🏷️ Groups", open=False)
        for g in s['groups']:
            info = self.project.groups.get(g, {})
            self.tree.insert(grp_node, 'end', text=f"● {g} - {info.get('name', '')}")

    def open_outputs_folder(self):
        if not self._require_project():
            return
        path = os.path.join(self.project.root, 'outputs')
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')

    def _require_project(self):
        if self.project is None:
            messagebox.showwarning('No project', 'Open or create a project first.')
            return False
        if len(self.project.sites) == 0:
            messagebox.showwarning('Empty project',
                                     'This project has 0 sites.\n'
                                     'Use File → Import stations CSV to add sites.')
            return False
        return True

    # ---------- pipeline ----------
    def run_step(self, key):
        if not self._require_project():
            return
        # Pre-processing confirmation dialog (for ERT/MASW only)
        if key in ('ert', 'masw') and _seem_settings is not None:
            if not _seem_settings.show_data_preview(self.root, self.project,
                                                      module=key):
                self._log(f'[~] {key} cancelled by user at confirmation.',
                           'warning')
                return
        card = self.step_cards[key]
        if card.state == 'running':
            return
        card.set_state('running')
        self._status(f"Running: {key}...")
        self._log(f'[>] Step: {key}', 'info')

        def worker():
            t_start = time.time()
            try:
                self._do_step(key)
                elapsed = time.time() - t_start
                card.set_state('done', timing=f'✓ {elapsed:.1f}s')
                self._log(f'[+] {key} done ({elapsed:.1f}s)', 'success')
                self._refresh_image_list()
            except Exception as e:
                card.set_state('failed', timing='✗ Failed')
                self._log(f'[!] {key} failed: {e}', 'error')
                messagebox.showerror(key, str(e))
            finally:
                self._status('Ready.')
        threading.Thread(target=worker, daemon=True).start()

    def run_mode_pipeline(self):
        """Run steps based on selected mode: ERT only, MASW only, or Both."""
        if not self._require_project():
            return
        mode = self.run_mode.get()
        # Pre-processing confirmation dialog
        if _seem_settings is not None:
            module = 'ert' if mode == 'ert' else ('masw' if mode == 'masw' else 'ert')
            if not _seem_settings.show_data_preview(self.root, self.project,
                                                      module=module):
                self._log('[~] Pipeline cancelled by user at confirmation.',
                           'warning')
                return
        # Build step list by mode
        if mode == 'ert':
            steps = [('gen_data', 'Shared'), ('ert', 'ERT'),
                      ('ert_fence', 'ERT'), ('kmz', 'Shared'), ('pdf', 'Shared')]
            masw_skip = ['masw', 'vs30', 'masw_fence']
            self._log(f'[>] Running ERT-only pipeline...', 'ert')
        elif mode == 'masw':
            steps = [('gen_data', 'Shared'), ('masw', 'MASW'),
                      ('vs30', 'MASW'), ('masw_fence', 'MASW'),
                      ('kmz', 'Shared'), ('pdf', 'Shared')]
            masw_skip = ['ert', 'ert_fence']
            self._log(f'[>] Running MASW-only pipeline...', 'masw')
        else:
            steps = [('gen_data', 'Shared'), ('ert', 'ERT'), ('masw', 'MASW'),
                      ('corr', 'Shared'), ('ert_fence', 'ERT'),
                      ('masw_fence', 'MASW'), ('vs30', 'MASW'),
                      ('kmz', 'Shared'), ('pdf', 'Shared')]
            masw_skip = []
            self._log(f'[>] Running FULL pipeline (ERT + MASW)...', 'info')

        for s in masw_skip:
            if s in self.step_cards:
                self.step_cards[s].set_state('skipped', timing='Not in this mode')

        def worker():
            self.run_btn.config(state='disabled')
            self._status(f'Running {mode} pipeline...')
            for key, grp in steps:
                if key not in self.step_cards:
                    continue
                card = self.step_cards[key]
                card.set_state('running')
                self._log(f'[>] {grp}: {key}', grp.lower() if grp in ('ERT', 'MASW') else 'info')
                t_start = time.time()
                try:
                    self._do_step(key)
                    elapsed = time.time() - t_start
                    card.set_state('done', timing=f'✓ {elapsed:.1f}s')
                    self._log(f'[+] {key} done ({elapsed:.1f}s)', 'success')
                except Exception as e:
                    card.set_state('failed', timing='✗ Failed')
                    self._log(f'[!] {key} failed: {e}', 'error')
                self._refresh_image_list()
            self._status('Pipeline complete.')
            self._log(f'[+] {mode.upper()} PIPELINE COMPLETE', 'success')
            self.run_btn.config(state='normal')
            messagebox.showinfo('Done', f'{mode.upper()} pipeline complete!')
        threading.Thread(target=worker, daemon=True).start()

    def _do_step(self, key):
        p = self.project
        if key == 'gen_data':
            from seem_geo.data.realistic_field_generator import generate_project_data
            generate_project_data(p)
        elif key == 'ert':
            os.makedirs(p.ert_output_dir, exist_ok=True)
            from seem_geo.core.ert import batch_ert
            r = batch_ert(p)
            self._result(f'\nERT: {len(r)} stations inverted', 'ert')
        elif key == 'masw':
            os.makedirs(p.masw_output_dir, exist_ok=True)
            from seem_geo.core.masw import batch_masw
            r = batch_masw(p)
            self._result(f'\nMASW: {len(r)} stations processed', 'masw')
        elif key == 'corr':
            from seem_geo.core.correlations import build_correlations
            stats = build_correlations(p)
            self._result('\nCorrelations:', 'header')
            for k, v in stats.items():
                self._result(f"  {k}: R² = {v['r2']:.3f}, p = {v['p']:.2e}")
        elif key in ('ert_fence', 'masw_fence'):
            from seem_geo.core.fence import build_fence_diagrams
            build_fence_diagrams(p)
        elif key == 'vs30':
            from seem_geo.reports.vs30_map import build_vs30_bar_chart
            build_vs30_bar_chart(p)
        elif key == 'kmz':
            from seem_geo.io.kmz_exporter import export_results_kmz
            export_results_kmz(p)
        elif key == 'pdf':
            from seem_geo.reports.pdf_report import build_pdf_report
            out = build_pdf_report(p)
            self._result(f'\nPDF: {out}', 'success')

    # ---------- viewer ----------
    def _refresh_image_list(self):
        if not self.project:
            return
        self._all_images = {'ert_pseudo': [], 'ert_inv': [],
                             'masw_disp': [], 'masw_vs': [],
                             'corr': [], 'fence': [], 'reports': []}
        import glob
        for p in sorted(glob.glob(os.path.join(self.project.ert_output_dir, '*_pseudosection.png'))):
            self._all_images['ert_pseudo'].append(p)
        for p in sorted(glob.glob(os.path.join(self.project.ert_output_dir, '*_inverted.png'))):
            self._all_images['ert_inv'].append(p)
        for p in sorted(glob.glob(os.path.join(self.project.masw_output_dir, '*_dispersion.png'))):
            self._all_images['masw_disp'].append(p)
        for p in sorted(glob.glob(os.path.join(self.project.masw_output_dir, '*_vs_profile.png'))):
            self._all_images['masw_vs'].append(p)
        for p in sorted(glob.glob(os.path.join(self.project.correlation_output_dir, '*.png'))):
            self._all_images['corr'].append(p)
        for p in sorted(glob.glob(os.path.join(self.project.fence_output_dir, '*.png'))):
            self._all_images['fence'].append(p)
        for p in sorted(glob.glob(os.path.join(self.project.reports_dir, '*.png'))):
            self._all_images['reports'].append(p)
        self._refresh_viewer()

    def _refresh_viewer(self):
        mode = self.view_mode.get()
        if mode == 'single':
            # All individual images in dropdown
            items = []
            for cat in ('ert_pseudo', 'ert_inv', 'masw_disp', 'masw_vs',
                         'corr', 'fence', 'reports'):
                for p in self._all_images.get(cat, []):
                    items.append(os.path.basename(p))
        elif mode == 'ert_compare':
            # ERT line names (e.g., ERT-01 from ERT-01_pseudosection.png)
            items = sorted(set(os.path.basename(p).replace('_pseudosection.png', '')
                                for p in self._all_images.get('ert_pseudo', [])))
        else:  # masw_compare
            items = sorted(set(os.path.basename(p).replace('_dispersion.png', '')
                                for p in self._all_images.get('masw_disp', [])))
        self.image_dropdown['values'] = items
        if items:
            self.image_var.set(items[0])
            self._on_image_selected(None)

    def _on_image_selected(self, event):
        name = self.image_var.get()
        if not name:
            return
        mode = self.view_mode.get()
        try:
            self.viewer_fig.clear()
            t = self.theme
            self.viewer_fig.set_facecolor(t['panel'])
            if mode == 'single':
                # Find full path
                for cat in self._all_images.values():
                    for p in cat:
                        if os.path.basename(p) == name:
                            ax = self.viewer_fig.add_subplot(111)
                            ax.imshow(plt.imread(p)); ax.axis('off')
                            ax.set_title(name, fontsize=11, color=t['fg'])
                            break
            elif mode == 'ert_compare':
                pseudo = os.path.join(self.project.ert_output_dir, f'{name}_pseudosection.png')
                inv = os.path.join(self.project.ert_output_dir, f'{name}_inverted.png')
                ax1 = self.viewer_fig.add_subplot(211)
                if os.path.exists(pseudo):
                    ax1.imshow(plt.imread(pseudo))
                    ax1.set_title(f'{name} — Pseudosection (raw data)',
                                   fontsize=10, color=t['fg'])
                ax1.axis('off')
                ax2 = self.viewer_fig.add_subplot(212)
                if os.path.exists(inv):
                    ax2.imshow(plt.imread(inv))
                    ax2.set_title(f'{name} — Inverted (true resistivity)',
                                   fontsize=10, color=t['fg'])
                ax2.axis('off')
                self.viewer_fig.tight_layout()
            else:  # masw_compare
                disp = os.path.join(self.project.masw_output_dir, f'{name}_dispersion.png')
                vs = os.path.join(self.project.masw_output_dir, f'{name}_vs_profile.png')
                ax1 = self.viewer_fig.add_subplot(121)
                if os.path.exists(disp):
                    ax1.imshow(plt.imread(disp))
                    ax1.set_title(f'{name} — Dispersion', fontsize=10, color=t['fg'])
                ax1.axis('off')
                ax2 = self.viewer_fig.add_subplot(122)
                if os.path.exists(vs):
                    ax2.imshow(plt.imread(vs))
                    ax2.set_title(f'{name} — Vs profile', fontsize=10, color=t['fg'])
                ax2.axis('off')
                self.viewer_fig.tight_layout()
            self.viewer_canvas.draw()
        except Exception as e:
            self._log(f'Viewer error: {e}', 'error')

    # ---------- tools ----------
    def convert_syscal(self):
        files = filedialog.askopenfilenames(title='Choose SYSCAL Pro .bin files',
                                              filetypes=[('SYSCAL', '*.bin')])
        if not files:
            return
        out_dir = filedialog.askdirectory(title='Output folder')
        if not out_dir:
            return
        from seem_geo.io.importers import convert_syscal_to_res2dinv
        self._log(f'[>] Converting {len(files)} SYSCAL files...', 'info')

        def worker():
            ok = 0
            for f in files:
                base = os.path.splitext(os.path.basename(f))[0]
                out = os.path.join(out_dir, f'{base}.dat')
                try:
                    info = convert_syscal_to_res2dinv(f, out)
                    self._log(f'  [+] {base}: {info["n_records"]} records', 'success')
                    ok += 1
                except Exception as e:
                    self._log(f'  [!] {base}: {e}', 'error')
            messagebox.showinfo('SYSCAL Convert', f'Done: {ok}/{len(files)}')
        threading.Thread(target=worker, daemon=True).start()

    def launch_picker(self):
        f = filedialog.askopenfilename(title='MASW shot CSV',
                                         filetypes=[('CSV', '*.csv')])
        if not f:
            return
        from seem_geo.gui.dispersion_picker import launch_picker
        launch_picker(f)

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def open_image_settings(self):
        """Open the comprehensive 5-tab settings dialog."""
        if _seem_settings is None:
            messagebox.showwarning('Settings unavailable',
                                     'The seem_geo.settings module is not installed.\n'
                                     'Copy settings.py into the seem_geo package folder.')
            return
        saved = _seem_settings.show_dialog(self.root)
        if saved:
            img = saved.get('image', {})
            inv = saved.get('inversion', {})
            self._status(f'Settings saved — {img.get("dpi", "?")} DPI, '
                           f'{inv.get("method", "?")} inversion')
            self._log(f'Settings updated — DPI: {img.get("dpi")}, '
                       f'method: {inv.get("method")}, '
                       f'mesh: {inv.get("mesh_fineness")}, '
                       f'filters: {"on" if saved.get("filters", {}).get("remove_outliers") else "off"}',
                       'success')

    def compare_inversions(self):
        """Enable 'compare 3 methods' mode and prompt to run ERT."""
        if _seem_settings is None:
            return
        cfg = _seem_settings.load()
        cfg['inversion']['compare_methods'] = True
        _seem_settings.save(cfg)
        _seem_settings.apply(cfg)
        messagebox.showinfo('Compare Inversions',
                             'Comparison mode enabled.\n\n'
                             'Next ERT run will execute 3 methods:\n'
                             '  • Smoothness (Occam)\n'
                             '  • Robust (L1 norm)\n'
                             '  • Marquardt (ridge)\n\n'
                             'Each will produce separate output images for '
                             'side-by-side RMS comparison.\n\n'
                             'Note: This takes ~3× longer than a single run.')
        self._log('[>] Inversion comparison mode: ON '
                   '(3 methods will run on next ERT)', 'warning')

    def toggle_qc_pdf(self):
        """Toggle whether QC overlay panel is embedded in the PDF report."""
        if _seem_settings is None:
            return
        cfg = _seem_settings.load()
        new = not cfg['qc'].get('include_qc_in_pdf', False)
        cfg['qc']['include_qc_in_pdf'] = new
        _seem_settings.save(cfg)
        state = 'ENABLED' if new else 'DISABLED'
        messagebox.showinfo('QC in PDF Report',
                             f'QC panel in PDF report: {state}\n\n'
                             f'{"✓ Next PDF export will include RMS, iterations, DOI, Chi² chart" if new else "× PDF will show plots only (no QC overlay)"}')
        self._log(f'QC in PDF: {state}', 'info')

    def show_about(self):
        messagebox.showinfo('About',
                             'SEEM Geo Pro v3\n\n'
                             'ERT & MASW Processing Suite\n'
                             'MIT License\n\n'
                             'DOI: 10.5281/zenodo.23455148\n'
                             'github.com/ahmedezz33/SEEM-Geo')


def main():
    root = tk.Tk()
    SeemGeoProApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
