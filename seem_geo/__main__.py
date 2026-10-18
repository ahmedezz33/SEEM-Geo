"""
SEEM Geo CLI - unified command-line entry point.
"""
import os
import sys
import argparse

from seem_geo.core.project import SeemProject


def _print_banner():
    print("=" * 70)
    print("  SEEM Geo v1.1.0 - Professional ERT & MASW Processing Suite")
    print("  Open source - MIT License")
    print("=" * 70)


def cmd_init(args):
    _print_banner()
    proj = SeemProject.init_default(args.dir, name=args.name)
    print(f"\n[+] Created new project at: {proj.file}")
    print(f"    Name: {proj.config['project']['name']}")
    print(f"    Sites: {len(proj.sites)}")
    return 0


def cmd_info(args):
    _print_banner()
    proj = SeemProject.load(args.project)
    s = proj.summary()
    print(f"\nProject: {s['name']}")
    print(f"Root:    {s['root']}")
    print(f"Sites:   {s['n_sites']}")
    print(f"Groups:  {', '.join(s['groups'])}")
    return 0


def cmd_gen_data(args):
    _print_banner()
    from seem_geo.data.realistic_field_generator import generate_project_data
    proj = SeemProject.load(args.project)
    generate_project_data(proj)
    print(f"\n[+] Generated synthetic field data for {len(proj.sites)} sites.")
    return 0


def cmd_ert(args):
    _print_banner()
    from seem_geo.core.ert import batch_ert
    proj = SeemProject.load(args.project)
    os.makedirs(proj.ert_output_dir, exist_ok=True)
    print(f"\n[>] Processing ERT for {len(proj.sites)} sites...")
    results = batch_ert(proj, verbose=args.verbose)
    print(f"[+] ERT complete: {len(results)} stations processed.")
    return 0


def cmd_masw(args):
    _print_banner()
    from seem_geo.core.masw import batch_masw
    proj = SeemProject.load(args.project)
    os.makedirs(proj.masw_output_dir, exist_ok=True)
    print(f"\n[>] Processing MASW for {len(proj.sites)} sites...")
    results = batch_masw(proj, verbose=args.verbose)
    print(f"[+] MASW complete: {len(results)} stations processed.")
    return 0


def cmd_corr(args):
    _print_banner()
    from seem_geo.core.correlations import build_correlations
    proj = SeemProject.load(args.project)
    print(f"\n[>] Building correlation framework...")
    stats = build_correlations(proj)
    print(f"[+] Built {len(stats)} correlations.")
    for k, s in stats.items():
        print(f"    {k}: R^2 = {s['r2']:.3f}, p = {s['p']:.3e}, n = {s['n']}")
    return 0


def cmd_fence(args):
    _print_banner()
    from seem_geo.core.fence import build_fence_diagrams
    proj = SeemProject.load(args.project)
    print(f"\n[>] Building fence diagrams...")
    out = build_fence_diagrams(proj)
    for k, v in out.items():
        print(f"    {k}: {v}")
    return 0


def cmd_vs30_map(args):
    _print_banner()
    from seem_geo.reports.vs30_map import build_vs30_map, build_vs30_bar_chart
    proj = SeemProject.load(args.project)
    print(f"\n[>] Building Vs30 outputs...")
    bar_png = build_vs30_bar_chart(proj)
    print(f"    bar chart: {bar_png}")
    try:
        map_png = build_vs30_map(proj)
        print(f"    map:       {map_png}")
    except Exception as e:
        print(f"    map skipped (station coords not available): {e}")
    return 0


def cmd_kmz(args):
    _print_banner()
    from seem_geo.io.kmz_exporter import export_results_kmz
    proj = SeemProject.load(args.project)
    print(f"\n[>] Exporting KMZ...")
    out_kmz = export_results_kmz(proj)
    print(f"[+] KMZ written: {out_kmz}")
    return 0


def cmd_report(args):
    _print_banner()
    from seem_geo.reports.pdf_report import build_pdf_report
    proj = SeemProject.load(args.project)
    print(f"\n[>] Building PDF report...")
    out_pdf = build_pdf_report(proj)
    print(f"[+] PDF written: {out_pdf}")
    return 0


def cmd_import(args):
    _print_banner()
    from seem_geo.io.importers import convert_to_seem_ert_csv, convert_to_seem_masw_csv
    if args.type == 'ert':
        info = convert_to_seem_ert_csv(args.input, args.output)
    else:
        info = convert_to_seem_masw_csv(args.input, args.output)
    print(f"\n[+] Imported {info['input_format']}: {info['n_records']} records -> {info['output']}")
    return 0


def cmd_convert_syscal(args):
    """SYSCAL Pro .bin -> Res2DInv .dat batch converter."""
    _print_banner()
    import glob
    from seem_geo.io.importers import convert_syscal_to_res2dinv
    pattern = args.input
    outputs = []
    files = sorted(glob.glob(pattern, recursive=True)) if '*' in pattern else [pattern]
    if not files:
        print(f"[!] No files match: {pattern}")
        return 1
    os.makedirs(args.out_dir, exist_ok=True)
    print(f"\n[>] Converting {len(files)} SYSCAL Pro .bin file(s) -> Res2DInv .dat")
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        out_dat = os.path.join(args.out_dir, f'{base}.dat')
        try:
            info = convert_syscal_to_res2dinv(f, out_dat,
                                              electrode_spacing=args.spacing,
                                              filter_records=not args.no_filter)
            print(f"  [+] {base}: {info['n_records']} rec  "
                  f"rho=[{info['rho_a_min']:.1f}, {info['rho_a_max']:.1f}] mean={info['rho_a_mean']:.1f} Ohm.m")
            outputs.append(info)
        except Exception as e:
            print(f"  [!] {base} failed: {e}")
    print(f"\n[+] Converted {len(outputs)}/{len(files)} files.")
    return 0


def cmd_picker(args):
    _print_banner()
    from seem_geo.gui.dispersion_picker import launch_picker
    launch_picker(args.file)
    return 0


def cmd_gui(args):
    _print_banner()
    from seem_geo.gui.main_window import main as gui_main
    gui_main()
    return 0


def cmd_pipeline(args):
    _print_banner()
    print("\n[>] Running full pipeline (gen-data -> ERT -> MASW -> corr -> fence -> vs30 -> kmz -> report)")
    for fn, name in [(cmd_gen_data, 'gen-data'),
                     (cmd_ert, 'ert'),
                     (cmd_masw, 'masw'),
                     (cmd_corr, 'corr'),
                     (cmd_fence, 'fence'),
                     (cmd_vs30_map, 'vs30-map'),
                     (cmd_kmz, 'kmz'),
                     (cmd_report, 'report')]:
        print(f"\n--- step: {name} ---")
        try:
            fn(args)
        except Exception as e:
            print(f"[!] step '{name}' failed: {e}")
    print("\n[+] Pipeline complete.")
    return 0


def cmd_build_exe(args):
    _print_banner()
    print("\n[>] Running Windows .exe builder...")
    build_script = os.path.join(os.path.dirname(__file__), '..', 'build_windows.py')
    if os.path.exists(build_script):
        os.system(f"{sys.executable} {build_script}")
    else:
        print("[!] build_windows.py not found. Run from source checkout.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog='seem-geo',
        description='SEEM Geo - Professional ERT & MASW Processing Suite'
    )
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('init', help='Create a new project directory')
    p.add_argument('dir', help='Project directory to create')
    p.add_argument('--name', default='New Project')
    p.set_defaults(func=cmd_init)

    p = sub.add_parser('info', help='Show project summary')
    p.add_argument('project', help='Path to .seemproj file')
    p.set_defaults(func=cmd_info)

    p = sub.add_parser('gen-data', help='Generate realistic synthetic field data')
    p.add_argument('project', help='Path to .seemproj file')
    p.set_defaults(func=cmd_gen_data)

    p = sub.add_parser('import', help='Convert vendor files to SEEM CSV')
    p.add_argument('--type', choices=['ert', 'masw'], required=True)
    p.add_argument('input', help='Input file')
    p.add_argument('output', help='Output CSV path')
    p.set_defaults(func=cmd_import)

    p = sub.add_parser('convert-syscal',
                       help='Convert IRIS SYSCAL Pro .bin -> Res2DInv .dat (glob supported)')
    p.add_argument('input', help='Path or glob (e.g. "ERT*/*.bin")')
    p.add_argument('--out-dir', required=True, help='Output directory for .dat files')
    p.add_argument('--spacing', type=float, default=2.0,
                   help='Electrode spacing in meters (default 2.0)')
    p.add_argument('--no-filter', action='store_true',
                   help='Skip quality filtering (keep all records)')
    p.set_defaults(func=cmd_convert_syscal)

    p = sub.add_parser('ert', help='Run ERT inversion batch')
    p.add_argument('project')
    p.add_argument('--verbose', action='store_true')
    p.set_defaults(func=cmd_ert)

    p = sub.add_parser('masw', help='Run MASW processing batch')
    p.add_argument('project')
    p.add_argument('--verbose', action='store_true')
    p.set_defaults(func=cmd_masw)

    p = sub.add_parser('corr', help='Build correlation framework')
    p.add_argument('project')
    p.set_defaults(func=cmd_corr)

    p = sub.add_parser('fence', help='Build fence diagrams')
    p.add_argument('project')
    p.set_defaults(func=cmd_fence)

    p = sub.add_parser('vs30-map', help='Build Vs30 map + bar chart')
    p.add_argument('project')
    p.set_defaults(func=cmd_vs30_map)

    p = sub.add_parser('kmz', help='Export results to Google Earth KMZ')
    p.add_argument('project')
    p.set_defaults(func=cmd_kmz)

    p = sub.add_parser('report', help='Build PDF report')
    p.add_argument('project')
    p.set_defaults(func=cmd_report)

    p = sub.add_parser('picker', help='Launch interactive dispersion picker')
    p.add_argument('file', help='MASW shot CSV')
    p.set_defaults(func=cmd_picker)

    p = sub.add_parser('gui', help='Launch desktop GUI')
    p.set_defaults(func=cmd_gui)

    p = sub.add_parser('pipeline', help='Run full pipeline end-to-end')
    p.add_argument('project')
    p.add_argument('--verbose', action='store_true')
    p.set_defaults(func=cmd_pipeline)

    p = sub.add_parser('build-exe', help='Build Windows .exe (requires PyInstaller)')
    p.set_defaults(func=cmd_build_exe)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
