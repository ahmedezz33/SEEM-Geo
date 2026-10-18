"""
Industry-Standard Importers for ERT & MASW Field Files
Supports:
  ERT:  Res2DInv (.dat / .urf), AGI SuperSting (.stg), ABEM-Lund (.ohm),
        IRIS Instruments SYSCAL Pro (.bin)
  MASW: SurfSeis (.dc dispersion), SEG2 (.sg2), SEG-Y (.sgy), ASCII
"""
import os
import re
import struct
import numpy as np
import pandas as pd


# =============================================================================
# SYSCAL PRO .bin FORMAT (IRIS Instruments)
# =============================================================================

# Reverse-engineered from field files acquired with SYSCAL Pro V11
SYSCAL_HEADER_SIZE = 1333   # bytes before first record
SYSCAL_RECORD_SIZE = 304    # bytes per measurement record

# Offsets inside each record (from byte 16, where A begins)
_OFF_A = 16
_OFF_B = 20
_OFF_M = 24
_OFF_N = 28
# Offsets inside the measurement payload (starts at byte 32)
_PAY_VP = 32   # Vp (mV)
_PAY_DEV = 36  # Dev (%)
_PAY_RHO = 40  # rho_a (Ohm.m) — the instrument's own computed apparent resistivity
_PAY_I = 44    # Current I (mA)


def _dd_geometric_factor(A, B, M, N):
    """Dipole-dipole 2*pi / (1/AM - 1/AN - 1/BM + 1/BN)."""
    def inv_d(p1, p2):
        d = abs(p1 - p2)
        return 1.0 / d if d > 1e-6 else 0.0
    denom = inv_d(A, M) - inv_d(A, N) - inv_d(B, M) + inv_d(B, N)
    return 2.0 * np.pi / denom if abs(denom) > 1e-9 else 0.0


def read_syscal_pro_bin(path):
    """Parse an IRIS Instruments SYSCAL Pro .bin file.

    Returns (DataFrame, meta_dict).  DataFrame columns:
      A, B, M, N          electrode positions (m)
      Vp_mV, I_mA, dev_pct  raw measurements
      rho_a               apparent resistivity (Ohm.m) as recorded by the instrument
      K                   geometric factor computed from ABMN
      x, a, z_pseudo      Res2DInv-style coordinates (center of A-B dipole, dipole length, pseudo-depth)
    """
    with open(path, 'rb') as fh:
        data = fh.read()
    sz = len(data)
    if sz < SYSCAL_HEADER_SIZE + SYSCAL_RECORD_SIZE:
        raise ValueError(f'File too small for SYSCAL Pro format: {sz} bytes')
    n_rec = (sz - SYSCAL_HEADER_SIZE) // SYSCAL_RECORD_SIZE
    rows = []
    for i in range(n_rec):
        off = SYSCAL_HEADER_SIZE + i * SYSCAL_RECORD_SIZE
        rec = data[off:off + SYSCAL_RECORD_SIZE]
        a = struct.unpack('<f', rec[_OFF_A:_OFF_A + 4])[0]
        b = struct.unpack('<f', rec[_OFF_B:_OFF_B + 4])[0]
        m = struct.unpack('<f', rec[_OFF_M:_OFF_M + 4])[0]
        n = struct.unpack('<f', rec[_OFF_N:_OFF_N + 4])[0]
        vp = struct.unpack('<f', rec[32 + _PAY_VP:32 + _PAY_VP + 4])[0]
        dev = struct.unpack('<f', rec[32 + _PAY_DEV:32 + _PAY_DEV + 4])[0]
        rho_a = struct.unpack('<f', rec[32 + _PAY_RHO:32 + _PAY_RHO + 4])[0]
        current = struct.unpack('<f', rec[32 + _PAY_I:32 + _PAY_I + 4])[0]
        rows.append({'A': a, 'B': b, 'M': m, 'N': n,
                     'Vp_mV': vp, 'I_mA': current, 'rho_a': rho_a, 'dev_pct': dev})
    df = pd.DataFrame(rows)
    # Add geometric factor, Res2DInv-friendly coords
    df['K'] = df.apply(lambda r: _dd_geometric_factor(r['A'], r['B'], r['M'], r['N']), axis=1)
    df['x'] = (df['A'] + df['B']) / 2.0           # center of first dipole
    df['a'] = (df['B'] - df['A']).abs()           # dipole length
    df['z_pseudo'] = ((df['M'] + df['N']) / 2.0 - (df['A'] + df['B']) / 2.0).abs() / 3.0
    meta = {'format': 'IRIS SYSCAL Pro', 'n_records_raw': n_rec,
            'header_size': SYSCAL_HEADER_SIZE, 'record_size': SYSCAL_RECORD_SIZE}
    return df, meta


def filter_syscal_records(df, max_dev=10.0, min_rho=0.1, max_rho=100000.0,
                          min_current=0.01):
    """Quality filter: drop null, out-of-range, or high-deviation records."""
    mask = ((df['A'] != 0) | (df['B'] != 0) | (df['M'] != 0) | (df['N'] != 0))
    mask &= df['rho_a'].abs().between(min_rho, max_rho)
    mask &= df['rho_a'].notna() & np.isfinite(df['rho_a'])
    mask &= df['I_mA'].abs() >= min_current
    if 'dev_pct' in df.columns:
        mask &= df['dev_pct'].abs() <= max_dev
    return df[mask].reset_index(drop=True)


def write_res2dinv_general(df, out_path, title='Converted from SYSCAL Pro',
                           electrode_spacing=2.0):
    """Write a Res2DInv general-array (type 11) .dat file from a SYSCAL DataFrame.

    df must contain columns A, B, M, N (meters) and rho_a (Ohm.m).
    """
    if len(df) == 0:
        raise ValueError('Empty DataFrame — nothing to write')
    with open(out_path, 'w') as f:
        f.write(f'{title}\n')
        f.write(f'{electrode_spacing:.2f}\n')
        f.write('11\n')                                  # general array
        f.write('0\n')                                   # sub-type: user-defined
        f.write('Type of measurement (0=app. res, 1=resistance)\n')
        f.write('0\n')                                   # apparent resistivity
        f.write(f'{len(df)}\n')                          # n_data
        f.write('2\n')                                   # x location is in metres
        f.write('0\n')                                   # no IP
        for _, r in df.iterrows():
            f.write(f"4   {r['A']:.2f} 0  {r['B']:.2f} 0  "
                    f"{r['M']:.2f} 0  {r['N']:.2f} 0  "
                    f"{abs(r['rho_a']):.4f}\n")
        f.write('0\n0\n0\n0\n')
    return out_path


def convert_syscal_to_res2dinv(bin_path, out_dat, title=None,
                               filter_records=True, electrode_spacing=2.0):
    """Convenience: one-call SYSCAL .bin -> Res2DInv .dat conversion."""
    df, meta = read_syscal_pro_bin(bin_path)
    if filter_records:
        df = filter_syscal_records(df)
    if title is None:
        title = f'SYSCAL Pro -> Res2DInv ({os.path.basename(bin_path)})'
    write_res2dinv_general(df, out_dat, title=title,
                           electrode_spacing=electrode_spacing)
    return {'input': bin_path, 'output': out_dat, 'n_records': len(df),
            'rho_a_min': float(df['rho_a'].abs().min()),
            'rho_a_max': float(df['rho_a'].abs().max()),
            'rho_a_mean': float(df['rho_a'].abs().mean()),
            'format_in': meta['format']}


# =============================================================================
# ERT IMPORTERS
# =============================================================================

def read_res2dinv_general(path):
    """Res2DInv general-array format (.dat)."""
    with open(path, 'r') as f:
        lines = [l.strip() for l in f.readlines()]
    title = lines[0]
    a_unit = float(lines[1])
    array_type = int(float(lines[2]))
    n_data = int(float(lines[3]))
    records = []
    for i in range(6, 6 + n_data):
        parts = lines[i].split()
        if len(parts) >= 3:
            try:
                x, a, rho = float(parts[0]), float(parts[1]), float(parts[2])
                records.append({'x': x, 'a': a, 'z_pseudo': a / 2.0, 'rho_a': rho})
            except ValueError:
                continue
    df = pd.DataFrame(records)
    return df, {'title': title, 'array_type': array_type, 'a_unit': a_unit}


def read_agi_superstng(path):
    """AGI SuperSting R8 .stg format - comma-separated with header."""
    data = []
    header = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                header[k.strip()] = v.strip()
                continue
            parts = line.split(',')
            if len(parts) >= 15:
                try:
                    I_ma = float(parts[3])
                    V_mv = float(parts[4])
                    v_over_i = float(parts[5])
                    A, B, M, N = (float(parts[9]), float(parts[10]),
                                  float(parts[11]), float(parts[12]))
                    AM = abs(M - A)
                    MN = abs(N - M)
                    NB = abs(B - N)
                    if abs(AM - MN) < 0.1 and abs(MN - NB) < 0.1:
                        a = AM
                        x_centre = (A + B) / 2
                        rho_a = 2 * np.pi * a * v_over_i
                        data.append({'x': x_centre, 'a': a,
                                     'z_pseudo': a / 2, 'rho_a': rho_a,
                                     'current_ma': I_ma, 'voltage_mv': V_mv})
                except (ValueError, IndexError):
                    continue
    return pd.DataFrame(data), header


def read_abem_lund(path):
    """ABEM-Lund (.ohm, .amp, .4) protocol - plain ASCII table."""
    data = []
    with open(path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    x, a = float(parts[0]), float(parts[1])
                    rho = float(parts[-1])
                    data.append({'x': x, 'a': a, 'z_pseudo': a / 2, 'rho_a': rho})
                except ValueError:
                    continue
    return pd.DataFrame(data), {}


def detect_and_read_ert(path):
    """Auto-detect format and dispatch."""
    ext = os.path.splitext(path)[1].lower()
    with open(path, 'r', errors='ignore') as f:
        head = f.read(500)
    if ext == '.stg' or 'SuperSting' in head:
        return read_agi_superstng(path), 'AGI SuperSting'
    if ext in ('.ohm', '.amp'):
        return read_abem_lund(path), 'ABEM-Lund'
    if ext == '.dat':
        return read_res2dinv_general(path), 'Res2DInv general'
    try:
        return read_res2dinv_general(path), 'Res2DInv general'
    except Exception:
        df = pd.read_csv(path)
        return (df, {}), 'CSV'


# =============================================================================
# MASW IMPORTERS
# =============================================================================

def read_surfseis_dc(path):
    """SurfSeis .dc dispersion file (text)."""
    picks = {'fundamental': []}
    current_mode = 'fundamental'
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith('#mode'):
                m = re.search(r'(\d+)', line)
                if m:
                    mode_n = int(m.group(1))
                    current_mode = 'fundamental' if mode_n == 0 else f'higher_mode_{mode_n}'
                continue
            if line.startswith('#') or line.startswith(';'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    f_hz, v_ms = float(parts[0]), float(parts[1])
                    picks.setdefault(current_mode, []).append((f_hz, v_ms))
                except ValueError:
                    continue
    if picks['fundamental']:
        df = pd.DataFrame(picks['fundamental'], columns=['freq_hz', 'phase_vel_ms'])
    else:
        df = pd.DataFrame(columns=['freq_hz', 'phase_vel_ms'])
    return df, {'all_modes': {k: pd.DataFrame(v, columns=['freq_hz', 'phase_vel_ms'])
                              for k, v in picks.items() if v}}


def read_seg2(path):
    """SEG-2 seismic data format - common for engineering seismic."""
    with open(path, 'rb') as f:
        raw = f.read()
    block_id = raw[:2]
    if block_id not in (b'\x55\x3a', b'\x3a\x55'):
        raise ValueError(f'Not a SEG-2 file (bad magic: {block_id})')
    endian = '<' if block_id == b'\x55\x3a' else '>'
    rev = struct.unpack(f'{endian}H', raw[2:4])[0]
    n_traces = struct.unpack(f'{endian}H', raw[6:8])[0]
    trace_offsets = []
    for i in range(n_traces):
        off = struct.unpack(f'{endian}I', raw[32 + i * 4: 36 + i * 4])[0]
        trace_offsets.append(off)
    traces = []
    geo_x = []
    for i, off in enumerate(trace_offsets):
        trace_header = raw[off:off + 32]
        trace_block_size = struct.unpack(f'{endian}H', trace_header[2:4])[0]
        n_samples = struct.unpack(f'{endian}I', trace_header[8:12])[0]
        data_fmt = struct.unpack(f'{endian}B', trace_header[12:13])[0]
        strings_start = off + 32
        strings_end = off + trace_block_size
        strings_raw = raw[strings_start:strings_end].decode('latin-1', errors='ignore')
        rx_loc = 0.0
        m = re.search(r'RECEIVER_LOCATION\s+([\d.-]+)', strings_raw)
        if m:
            rx_loc = float(m.group(1))
        geo_x.append(rx_loc)
        data_start = off + trace_block_size
        sz_map = {1: 2, 2: 4, 3: 4, 4: 4, 5: 8}
        data_end = data_start + n_samples * sz_map.get(data_fmt, 4)
        if data_fmt == 1:
            samples = np.frombuffer(raw[data_start:data_end], dtype=f'{endian}i2')
        elif data_fmt == 2:
            samples = np.frombuffer(raw[data_start:data_end], dtype=f'{endian}i4')
        elif data_fmt == 4:
            samples = np.frombuffer(raw[data_start:data_end], dtype=f'{endian}f4')
        elif data_fmt == 5:
            samples = np.frombuffer(raw[data_start:data_end], dtype=f'{endian}f8')
        else:
            samples = np.frombuffer(raw[data_start:data_end], dtype=f'{endian}f4')
        traces.append(samples)
    n_t = max(len(t) for t in traces)
    traces_arr = np.zeros((n_t, len(traces)))
    for i, t in enumerate(traces):
        traces_arr[:len(t), i] = t
    df = pd.DataFrame(traces_arr, columns=[f'{x:.1f}' for x in geo_x])
    return df, {'n_traces': n_traces, 'rev': rev, 'format_code': data_fmt}


def read_segy(path, sr_hz=None):
    """SEG-Y (SEG Y rev 1) seismic file reader (simplified)."""
    with open(path, 'rb') as f:
        raw = f.read()
    bin_header = raw[3200:3600]
    sample_interval_us = struct.unpack('>H', bin_header[16:18])[0]
    n_samples = struct.unpack('>H', bin_header[20:22])[0]
    data_fmt = struct.unpack('>H', bin_header[24:26])[0]
    if sr_hz is None:
        sr_hz = 1e6 / sample_interval_us if sample_interval_us > 0 else 2000
    offset = 3600
    trace_size = 240 + n_samples * 4
    n_traces = (len(raw) - 3600) // trace_size
    traces = np.zeros((n_samples, n_traces))
    geo_x = []
    for i in range(n_traces):
        hdr = raw[offset:offset + 240]
        rx = struct.unpack('>i', hdr[80:84])[0]
        geo_x.append(float(rx))
        data_bytes = raw[offset + 240:offset + trace_size]
        samples = np.frombuffer(data_bytes, dtype='>f4')
        traces[:, i] = samples[:n_samples]
        offset += trace_size
    df = pd.DataFrame(traces, columns=[f'{x:.1f}' for x in geo_x])
    return df, {'n_traces': n_traces, 'sr_hz': sr_hz, 'n_samples': n_samples,
                'format_code': data_fmt}


def detect_and_read_masw(path):
    """Auto-detect MASW file format and dispatch."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.dc', '.ms'):
        return read_surfseis_dc(path), 'SurfSeis DC'
    if ext in ('.sg2', '.seg2', '.dat'):
        try:
            return read_seg2(path), 'SEG-2'
        except (ValueError, IndexError):
            pass
    if ext in ('.sgy', '.segy'):
        return read_segy(path), 'SEG-Y'
    df = pd.read_csv(path)
    return (df, {}), 'CSV'


# =============================================================================
# CONVERT TO SEEM-GEO INTERNAL FORMAT
# =============================================================================

def convert_to_seem_ert_csv(input_path, output_csv):
    """Read any supported ERT format and write SEEM-standard CSV."""
    (df, meta), fmt = detect_and_read_ert(input_path)
    df.to_csv(output_csv, index=False)
    return {'input_format': fmt, 'n_records': len(df), 'output': output_csv, 'meta': meta}


def convert_to_seem_masw_csv(input_path, output_csv):
    """Read any supported MASW format and write SEEM-standard CSV."""
    (df, meta), fmt = detect_and_read_masw(input_path)
    df.to_csv(output_csv, index=False)
    return {'input_format': fmt, 'n_records': df.shape[0], 'n_channels': df.shape[1],
            'output': output_csv, 'meta': meta}
