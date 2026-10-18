"""
KMZ Exporter - Google Earth output of ERT/MASW results.
Produces a .kmz file with station placemarks and a corridor polyline.
Coordinates are generic / fictional for the demonstration dataset.
"""
import os
import zipfile
import pandas as pd


GROUP_COLORS_KML = {
    'G1': 'ff40ec2e',  # KML uses aabbggrr; green
    'G2': 'ff3641ff',  # red
    'G3': 'ff00dcff',  # yellow
    'G5': 'ffc90db1',  # purple
}


def _station_placemark(bh, lat, lon, grp, vs30, site_class, rho_mean, ucs, rqd):
    color = GROUP_COLORS_KML.get(grp, 'ffffffff')
    desc = (f"<![CDATA[<b>{bh}</b> (Group {grp})<br/>"
            f"Vs30: {vs30:.0f} m/s<br/>"
            f"Site class: {site_class}<br/>"
            f"rho_mean: {rho_mean:.0f} Ohm.m<br/>"
            f"UCS: {ucs:.1f} MPa<br/>"
            f"RQD: {rqd:.0f} %]]>")
    return f"""  <Placemark>
    <name>{bh}</name>
    <description>{desc}</description>
    <styleUrl>#style_{grp}</styleUrl>
    <Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point>
  </Placemark>"""


def _style_block():
    styles = []
    for grp, color in GROUP_COLORS_KML.items():
        styles.append(f"""  <Style id="style_{grp}">
    <IconStyle>
      <color>{color}</color>
      <scale>1.2</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/wht-circle.png</href></Icon>
    </IconStyle>
    <LabelStyle><scale>0.8</scale></LabelStyle>
  </Style>""")
    return '\n'.join(styles)


def _generate_coords(sites):
    """Generate fictional UTM-based lat/lon for demonstration."""
    # Use chainage along a fictional corridor (demo coords only).
    lat0, lon0 = 40.0, -74.0  # generic / fictional
    rows = []
    for s in sites:
        km = s.get('chainage_km', 0.0)
        # ~0.009 deg per km east
        lon = lon0 + km * 0.009
        lat = lat0 + km * 0.001
        rows.append({'bh': s['bh'], 'lat': lat, 'lon': lon,
                     'group': s['group']})
    return pd.DataFrame(rows)


def export_results_kmz(project, out_kmz=None):
    if out_kmz is None:
        out_kmz = os.path.join(project.reports_dir, 'SEEM_Geo_results.kmz')
    os.makedirs(os.path.dirname(out_kmz), exist_ok=True)

    df_coords = _generate_coords(project.sites)

    # Pull Vs30 and rho_mean from summaries if present
    masw_sum = os.path.join(project.masw_output_dir, 'MASW_summary.csv')
    ert_sum = os.path.join(project.ert_output_dir, 'ERT_summary.csv')
    df_vs = pd.read_csv(masw_sum) if os.path.exists(masw_sum) else pd.DataFrame()
    df_rho = pd.read_csv(ert_sum) if os.path.exists(ert_sum) else pd.DataFrame()

    placemarks = []
    coord_pairs = []
    for s in project.sites:
        bh = s['bh']
        row = df_coords[df_coords['bh'] == bh].iloc[0]
        vs_row = df_vs[df_vs['bh'] == bh] if 'bh' in df_vs.columns else pd.DataFrame()
        rho_row = df_rho[df_rho['bh'] == bh] if 'bh' in df_rho.columns else pd.DataFrame()
        vs30 = float(vs_row['vs30_ms'].iloc[0]) if len(vs_row) else 0.0
        site_class = vs_row['site_class'].iloc[0] if len(vs_row) else 'N/A'
        rho_mean = float(rho_row['rho_model_mean'].iloc[0]) if len(rho_row) else 0.0
        placemarks.append(_station_placemark(
            bh, row['lat'], row['lon'], s['group'],
            vs30, site_class, rho_mean,
            s.get('ucs_mpa', 0), s.get('rqd_pct', 0)))
        coord_pairs.append(f"{row['lon']:.6f},{row['lat']:.6f},0")

    corridor_line = f"""  <Placemark>
    <name>Corridor centreline</name>
    <Style><LineStyle><color>ff0000ff</color><width>2</width></LineStyle></Style>
    <LineString><coordinates>
      {' '.join(coord_pairs)}
    </coordinates></LineString>
  </Placemark>"""

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>SEEM Geo results - {project.config['project']['name']}</name>
  <description>Open-source ERT &amp; MASW results. Coordinates are generic for demonstration.</description>
{_style_block()}
{chr(10).join(placemarks)}
{corridor_line}
</Document>
</kml>"""

    with zipfile.ZipFile(out_kmz, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('doc.kml', kml)
    return out_kmz
