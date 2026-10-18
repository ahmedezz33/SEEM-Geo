"""
PDF report generator - compiles all SEEM Geo outputs into a single PDF.
Uses matplotlib backend_pdf so no external LaTeX/wkhtmltopdf is needed.
"""
import os
import glob
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def _title_page(pdf, project):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.5, 0.82, 'SEEM Geo', ha='center', fontsize=36,
             fontweight='bold', color='#1F4E79')
    fig.text(0.5, 0.76, 'Professional ERT & MASW Processing Suite',
             ha='center', fontsize=14, color='#555555')
    fig.text(0.5, 0.65, project.config['project']['name'],
             ha='center', fontsize=20, fontweight='bold')
    fig.text(0.5, 0.60, project.config['project'].get('description', ''),
             ha='center', fontsize=11, color='#555555', wrap=True)
    fig.text(0.5, 0.45, f"Report generated for {len(project.sites)} sites",
             ha='center', fontsize=12)
    fig.text(0.5, 0.40, 'Open source - MIT License',
             ha='center', fontsize=10, style='italic', color='#777777')
    plt.axis('off')
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def _summary_page(pdf, project):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.1, 0.95, 'Executive Summary', fontsize=18, fontweight='bold')
    y = 0.88
    masw_sum = os.path.join(project.masw_output_dir, 'MASW_summary.csv')
    ert_sum = os.path.join(project.ert_output_dir, 'ERT_summary.csv')
    text_lines = []
    if os.path.exists(ert_sum):
        df = pd.read_csv(ert_sum)
        text_lines.append(f"ERT inversions:   {len(df)} stations complete")
        text_lines.append(f"  rho_a range:    {df['rho_a_min'].min():.0f} - {df['rho_a_max'].max():.0f} Ohm.m")
        text_lines.append(f"  Mean RMS:       {df['final_rms'].mean():.4f}")
    if os.path.exists(masw_sum):
        df = pd.read_csv(masw_sum)
        text_lines.append("")
        text_lines.append(f"MASW stations:    {len(df)} processed")
        text_lines.append(f"  Vs30 range:     {df['vs30_ms'].min():.0f} - {df['vs30_ms'].max():.0f} m/s")
        text_lines.append(f"  Mean Vs30:      {df['vs30_ms'].mean():.0f} m/s")
    for line in text_lines:
        fig.text(0.1, y, line, fontsize=11, family='monospace')
        y -= 0.028
    plt.axis('off')
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def _image_page(pdf, img_path, caption=""):
    if not os.path.exists(img_path):
        return
    try:
        img = plt.imread(img_path)
    except Exception:
        return
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_axes([0.05, 0.10, 0.90, 0.80])
    ax.imshow(img)
    ax.axis('off')
    if caption:
        fig.text(0.5, 0.06, caption, ha='center', fontsize=10,
                 style='italic', color='#555555')
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def _table_page(pdf, df, title):
    if df is None or len(df) == 0:
        return
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.5, 0.95, title, ha='center', fontsize=14, fontweight='bold')
    ax = fig.add_axes([0.05, 0.1, 0.90, 0.80])
    ax.axis('off')
    df_disp = df.copy()
    for c in df_disp.select_dtypes(include=[np.floating]).columns:
        df_disp[c] = df_disp[c].round(2)
    tbl = ax.table(cellText=df_disp.values,
                   colLabels=df_disp.columns,
                   loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1.0, 1.4)
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def build_pdf_report(project, out_pdf=None):
    if out_pdf is None:
        out_pdf = os.path.join(project.reports_dir, 'SEEM_Geo_Report.pdf')
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)

    with PdfPages(out_pdf) as pdf:
        _title_page(pdf, project)
        _summary_page(pdf, project)

        # Correlation plots
        corr_dir = project.correlation_output_dir
        if os.path.exists(corr_dir):
            for png in sorted(glob.glob(os.path.join(corr_dir, 'corr_*.png'))):
                _image_page(pdf, png,
                            caption=f"Correlation: {os.path.basename(png).replace('corr_', '').replace('.png', '')}")

        # Fence diagrams
        fence_dir = project.fence_output_dir
        for name in ('ERT_fence_diagram.png', 'MASW_fence_diagram.png',
                     'Corridor_ribbon.png'):
            p = os.path.join(fence_dir, name)
            if os.path.exists(p):
                _image_page(pdf, p, caption=name.replace('.png', '').replace('_', ' '))

        # Vs30 outputs
        for name in ('Vs30_bar_chart.png', 'Vs30_site_class_map.png'):
            p = os.path.join(project.reports_dir, name)
            if os.path.exists(p):
                _image_page(pdf, p, caption=name.replace('.png', '').replace('_', ' '))

        # Individual ERT inversions
        for site in project.sites[:4]:
            p = os.path.join(project.ert_output_dir,
                             f"{site['ert_id']}_inverted.png")
            if os.path.exists(p):
                _image_page(pdf, p,
                            caption=f"{site['bh']} - inverted true-resistivity section")

        # MASW dispersion and profiles for first few
        for site in project.sites[:4]:
            mw = site.get('masw_id', site['ert_id'].replace('ERT', 'MW'))
            for suffix in ('_dispersion.png', '_vs_profile.png'):
                p = os.path.join(project.masw_output_dir, f'{mw}{suffix}')
                if os.path.exists(p):
                    _image_page(pdf, p,
                                caption=f"{site['bh']} - {suffix[1:].replace('.png','').replace('_', ' ')}")

        # Summary tables
        ert_sum = os.path.join(project.ert_output_dir, 'ERT_summary.csv')
        if os.path.exists(ert_sum):
            _table_page(pdf, pd.read_csv(ert_sum), 'ERT Inversion Summary')
        masw_sum = os.path.join(project.masw_output_dir, 'MASW_summary.csv')
        if os.path.exists(masw_sum):
            _table_page(pdf, pd.read_csv(masw_sum), 'MASW / Vs30 Summary')
        master = os.path.join(project.correlation_output_dir, 'master_correlation_table.csv')
        if os.path.exists(master):
            _table_page(pdf, pd.read_csv(master), 'Master Correlation Table')
    return out_pdf
