# دليل الاستخدام الكامل — SEEM Geo

**نسخة 1.1 · العربية · شرح تفصيلي خطوة بخطوة**

---

## المحتويات

1. [التثبيت](#1-التثبيت)
2. [الهيكل العام للبرنامج](#2-الهيكل-العام)
3. [إنشاء مشروع جديد](#3-إنشاء-مشروع-جديد)
4. [تحضير البيانات الحقلية](#4-تحضير-البيانات)
5. [معالجة ERT (المقاومية الكهربائية)](#5-معالجة-ert)
6. [معالجة MASW (الموجات السطحية)](#6-معالجة-masw)
7. [الـ Dispersion Picker التفاعلي](#7-dispersion-picker)
8. [بناء الـ Correlations](#8-correlations)
9. [Fence Diagrams](#9-fence-diagrams)
10. [خريطة Vs30 و Site Class](#10-vs30-map)
11. [تصدير KMZ لـ Google Earth](#11-kmz-export)
12. [إنشاء تقرير PDF](#12-pdf-report)
13. [تشغيل الـ Pipeline كاملاً](#13-full-pipeline)
14. [استيراد ملفات Res2DInv / SurfSeis](#14-import)
15. [بناء ملف Windows .exe](#15-build-exe)

---

## 1. التثبيت

### المتطلبات
- **Python 3.8** أو أحدث
- **Git** (اختياري، لو عايز تسحب من GitHub)
- **Anaconda** أو **venv** (موصى به)

### الخطوات

#### أ) على Windows (Anaconda)
```bash
# افتح Anaconda Prompt
conda create -n seemgeo python=3.11
conda activate seemgeo

# انتقل لمجلد البرنامج
cd C:\path\to\geophysics_suite_pro

# ثبّت البرنامج
pip install -e .

# تأكد من التثبيت
seem-geo --help
```

#### ب) على Linux / Mac
```bash
python3 -m venv seemgeo_env
source seemgeo_env/bin/activate
cd /path/to/geophysics_suite_pro
pip install -e .
seem-geo --help
```

### الاعتماديات
البرنامج يحتاج هذي الحزم فقط (كلها شائعة):
- `numpy >= 1.21`
- `pandas >= 1.3`
- `scipy >= 1.7`
- `matplotlib >= 3.5`

**لا يحتاج** حزم خارجية معقدة زي `pygimli` أو `obspy`.

---

## 2. الهيكل العام

```
seem_geo/  ← الـ package الرئيسي
├── __main__.py  ← CLI (seem-geo command)
├── core/  ← المعالجة الأساسية
│  ├── project.py  ← إدارة ملفات المشاريع
│  ├── ert.py  ← معالجة ERT
│  ├── masw.py  ← معالجة MASW
│  ├── correlations.py  ← الـ 8 correlations
│  └── fence.py  ← Fence diagrams
├── gui/  ← واجهة Tkinter
│  ├── main_window.py  ← الواجهة الرئيسية
│  └── dispersion_picker.py ← Picker التفاعلي
├── io/  ← استيراد/تصدير
│  ├── importers.py  ← Res2DInv/SurfSeis/SEG-2
│  └── kmz_exporter.py  ← Google Earth KMZ
├── reports/  ← التقارير
│  ├── pdf_report.py  ← تقرير PDF 58 صفحة
│  └── vs30_map.py  ← خريطة Vs30
└── data/
  └── realistic_field_generator.py  ← مولّد بيانات اختبار
```

---

## 3. إنشاء مشروع جديد

### الطريقة الأولى — واجهة سطر الأوامر

```bash
seem-geo init --output my_project.seemproj
```

ده بينشئ ملف JSON بالإعدادات الافتراضية. افتحه بأي محرر نصوص وعدّله.

### الطريقة الثانية — من واجهة GUI

```bash
seem-geo gui
```
ثم: **File → New Project** → عدّل الحقول → **File → Save As**

### شكل ملف المشروع (`.seemproj`)

```json
{
  "project": {
  "name": "مشروع ممر مثال",
  "author": "أحمد",
  "institution": "مؤسستك"
  },
  "corridor": {
  "start_name": "Example West",
  "end_name": "Example East",
  "crs": "WGS 84 UTM (specify zone)",
  "azimuth_deg": 67.6,
  "length_km": 17.0
  },
  "acquisition": {
  "ert": {
  "array": "Wenner-alpha",
  "n_electrodes": 48,
  "spacing_m": 2.0,
  "spread_length_m": 100.0
  },
  "masw": {
  "n_geophones": 24,
  "spacing_m": 2.0,
  "spread_length_m": 46.0,
  "geophone_freq_hz": 4.5,
  "sampling_rate_hz": 2000
  }
  },
  "paths": {
  "ert_input": "data/ERT/",
  "masw_input": "data/MASW/",
  "bh_coordinates": "data/ERT_stations_v2.csv",
  "output_root": "output/"
  },
  "sites": [
  {"bh": "BH1", "group": "G3", "ert_id": "ERT-01", "masw_id": "MW-01",
  "rqd_mean": 28, "ucs_mpa": 5.8, "n60": 25, "w_grade": "V"},
  ...
  ]
}
```

**الحقول المهمة اللي لازم تعدّلها:**
- `paths.ert_input` — مجلد ملفات ERT بتاعتك
- `paths.masw_input` — مجلد ملفات MASW
- `paths.bh_coordinates` — ملف إحداثيات الآبار
- `paths.output_root` — مجلد المخرجات

---

## 4. تحضير البيانات

### تنسيق ERT (CSV لكل محطة)

ملف اسمه `ERT-01.csv` فيه:
```csv
x_center,electrode_a,current_i,voltage_v,rho_a
3,2,0.1,0.0026,0.33
5,2,0.1,0.0030,0.37
7,2,0.1,0.0028,0.35
...
```

| العمود | المعنى | الوحدة |
|---------|--------|---------|
| `x_center` | موقع منتصف الأقطاب الأربعة | m |
| `electrode_a` | المسافة بين الأقطاب (Wenner a) | m |
| `current_i` | التيار المحقون | A |
| `voltage_v` | فرق الجهد المقاس | V |
| `rho_a` | المقاومية الظاهرية (اختياري — تُحسب إذا لم تُعطَ) | Ω·m |

**البديل:** استخدم ملف Res2DInv `.dat` مباشرة — البرنامج يفهمه تلقائياً.

### تنسيق MASW (CSV لكل محطة)

ملف `MW-01_shot.csv`:
- **الصف الأول** = مواقع الـ geophones (0, 2, 4, ... 46 m)
- **كل صف بعدها** = عينة زمنية عبر 24 قناة

```csv
0.0,2.0,4.0,6.0,8.0,...,46.0
0.012,0.023,-0.015,0.008,...  ← t=0 s
0.034,-0.012,0.019,-0.007,...  ← t=0.0005 s
...
```

### تنسيق إحداثيات الآبار

ملف `ERT_stations_v2.csv`:
```csv
ERT_ID,BH_ref,Group,Center_E,Center_N,Center_Lat,Center_Lon,Elev_m,Start_E,Start_N,End_E,End_N,Start_Lat,Start_Lon,End_Lat,End_Lon,Length_m,Azimuth
ERT-01,BH1,G3,500000,4500000,40.610,0.015,900,...
```

---

## 5. معالجة ERT

### الخطوات داخل البرنامج

1. **قراءة بيانات Wenner** → pseudosection
2. **رسم الـ pseudosection** → ملف PNG
3. **عكس البيانات (Occam inversion)** → 2D true-resistivity model
4. **تصدير النموذج كـ CSV** للاستخدام في الـ correlations

### تشغيلها

```bash
# محطة واحدة
seem-geo ert --project my_project.seemproj -v

# المخرجات في: output/ERT/
#  ERT-01_pseudosection.png
#  ERT-01_inverted.png
#  ERT-01_model.csv
#  ... (لكل من الـ 12 محطة)
#  ERT_summary.csv
```

### قراءة النتائج

**`ERT-01_inverted.png`:**
- **المحور الأفقي** = المسافة على طول الـ spread (0-100 m)
- **المحور الرأسي** = العمق (0-30 m)
- **الألوان** = Resistivity على مقياس logarithmic:
  - أزرق (10-100 Ω·m) = Residual soil / تربة رطبة
  - أخضر-أصفر (100-500 Ω·m) = Weathered rock
  - أحمر (500-5000 Ω·m) = Fresh schist / granite

**الـ `_model.csv`:** جدول `(x_m, z_m, rho_ohm_m)` قابل لإعادة الاستخدام في برامج GIS.

---

## 6. معالجة MASW

### الخطوات

1. **قراءة shot gather** (24 trace × N samples)
2. **تحويل f-v (phase velocity)** بطريقة Slant-Stack
3. **التقاط dispersion curve** تلقائياً (أو يدوياً عبر Picker)
4. **عكس الـ dispersion** إلى Vs(z) باستخدام قاعدة λ/3
5. **حساب Vs30** و **تحديد Site Class** حسب applicable seismic design code

### تشغيلها

```bash
seem-geo masw --project my_project.seemproj -v
```

### قراءة النتائج

**`MW-01_fv_image.png`:**
- محور X = التردد (Hz)
- محور Y = Phase velocity (m/s)
- الألوان الدافئة = قوة إشارة قوية
- النقاط البيضاء = الـ picks (fundamental mode)

**`MW-01_vs_profile.png`:**
- Vs(z) مع خطوط حدود Site Class:
  - 180 m/s = حدود D|E
  - 360 m/s = حدود C|D
  - 760 m/s = حدود B|C

**`MASW_summary.csv`:**
```csv
station,vs30_ms,site_class,vs_min_ms,vs_max_ms
MW-01,291,D (stiff soil),120,357
MW-15,616,C (very dense),200,841
...
```

---

## 7. Dispersion Picker

### متى تستخدمه؟
لما الـ auto-pick مش دقيق، أو عندك higher modes، أو عايز تدقّق النتائج يدوياً.

### تشغيله

```bash
seem-geo picker --shot data/MASW/MW-15_shot.csv
```

### الاستخدام

| الفعل | النتيجة |
|-------|---------|
| **Left click** على f-v image | إضافة pick جديد |
| **Right click** قريب من pick | حذفه |
| **🤖 Auto-Pick** | التقاط تلقائي لأعلى peak في كل تردد |
| **🗑 Clear** | حذف كل الـ picks |
| **↩ Undo Last** | إلغاء آخر pick |
| **💾 Save Curve** | حفظ الـ dispersion كـ CSV |

### الـ Live Preview
على يمين الشاشة تلاقي:
- **Vs(z)** يُحدَّث لحظياً مع كل pick تضيفه
- **Vs30** محسوبة
- **Site Class** معروض بالاسم (A/B/C/D/E)

---

## 8. Correlations

### الـ 4 Correlations الأساسية

```bash
seem-geo corr --project my_project.seemproj
```

يبني:
1. **ρ vs RQD** (Group G1 Schist) — n=4
2. **Vs vs N₆₀** (Groups G3+G5) — n=6
3. **Vs vs RQD** (Group G1) — n=4
4. **Vs vs UCS** (Groups G1+G3) — n=7

### المخرجات

- `corr_1_rho_vs_RQD_G1.png` — scatter plot + خط الانحدار
- `calibration_data_at_depth.csv` — الجدول الكامل
- `correlation_results.json` — كل الإحصائيات (R², p-value, SE, CI)

### فهم الـ Statistical Status

| الحالة | المعنى |
|---------|---------|
| `ok` | n ≥ 5، الإحصائيات موثوقة |
| `min_df` | n=4، minimum degrees of freedom، CI واسع |
| `trend_line_only` | n=3، trend line فقط، R² غير موثوق |
| `descriptive_only` | n=2 (G2 فقط)، descriptive بس |

---

## 9. Fence Diagrams

```bash
seem-geo fence --project my_project.seemproj
```

**ثلاث مخرجات:**
1. **`fence_ERT.png`** — 12 ERT panel جنب بعض من الغرب للشرق
2. **`fence_MASW.png`** — 12 Vs(z) profile مرتبين
3. **`ribbon_resistivity.png`** — Resistivity ribbon مُستكمل على طول الممر

---

## 10. Vs30 Map

```bash
seem-geo vs30-map --project my_project.seemproj
```

**مخرجان:**
1. **`Vs30_site_class_map.png`** — خريطة UTM لـ 17 كم الممر، مُلوَّنة حسب Site Class
2. **`Vs30_bar_chart.png`** — Bar chart مرتب تنازلياً

### الفائدة
- يُظهر المناطق اللي محتاجة احتياطات زلزالية إضافية
- يُطابق مباشرة متطلبات applicable seismic design code Section 20

---

## 11. KMZ Export

```bash
seem-geo kmz --project my_project.seemproj
```

ينتج `SEEM_Geo_Results.kmz` — افتحه في **Google Earth** تلاقي:
- **12 نقطة** للآبار (ملوّنة حسب المجموعة: أخضر G1، أحمر G2، أصفر G3، بنفسجي G5)
- **12 خط ERT** (أزرق، 100 م)
- **12 خط MASW** (برتقالي، 46 م)
- **Popups تفاعلية** عند النقر على كل نقطة فيها: Vs30, Site Class, UCS, RQD, N₆₀

---

## 12. PDF Report

```bash
seem-geo report --project my_project.seemproj
```

ينتج `SEEM_Geo_Report.pdf` — 58 صفحة فيها:
1. **صفحة غلاف** باسم المشروع والمؤلف
2. **صفحة ملخص** — Vs30 وSite Class لكل محطة + كل الـ correlations
3. **24 صفحة ERT** — pseudosection + inverted section
4. **24 صفحة MASW** — f-v image + Vs(z)
5. **4 صفحات correlations**
6. **جدول calibration data**
7. **3 صفحات fence diagrams**

**جاهز للإلحاق بالفصل الخامس من الرسالة.**

---

## 13. Full Pipeline

**الطريقة الأسرع — تشغيل كل شيء بأمر واحد:**

```bash
seem-geo pipeline --project my_project.seemproj -v
```

ده بيشغّل الـ 7 مراحل بالترتيب:
1. ERT Processing (12 محطة)
2. MASW Processing (12 محطة)
3. Correlations (4 fits)
4. Fence Diagrams (3 outputs)
5. Vs30 Map (خريطة + chart)
6. KMZ Export
7. PDF Report

**الوقت المتوقع:** ~ 5-10 دقائق على جهاز متوسط.

---

## 14. استيراد Res2DInv / SurfSeis

### من Res2DInv (.dat)
```bash
seem-geo import --kind ert --input field_data.dat --output ERT-15.csv
```

### من AGI SuperSting (.stg)
```bash
seem-geo import --kind ert --input survey.stg --output ERT-23.csv
```

### من SurfSeis (.dc)
```bash
seem-geo import --kind masw --input MW-15.dc --output MW-15_dispersion.csv
```

### من SEG-2 (.sg2)
```bash
seem-geo import --kind masw --input shot_01.sg2 --output MW-15_shot.csv
```

### من SEG-Y (.sgy)
```bash
seem-geo import --kind masw --input shot_01.sgy --output MW-15_shot.csv
```

---

## 15. بناء Windows .exe

**على جهاز Windows:**

```bash
# ثبّت PyInstaller
pip install pyinstaller

# شغّل الـ builder
seem-geo build-exe
# أو
python build_windows.py
```

ينتج:
- **`dist/SEEM_Geo.exe`** — ملف واحد (~150 MB)، شغّال بدون Python
- **`dist/SEEM_Geo/`** — مجلد (أسرع في الفتح)

تقدر توزّع الـ `.exe` على زملاءك مباشرة.

---

## 📋 Cheat Sheet — كل الأوامر

```bash
seem-geo gui  # افتح الـ GUI
seem-geo init --output project.seemproj  # مشروع جديد
seem-geo info --project project.seemproj  # ملخص المشروع
seem-geo gen-data --out field_data/  # بيانات اختبار واقعية
seem-geo import --kind ert --input X --output Y
seem-geo ert --project project.seemproj -v  # ERT فقط
seem-geo masw --project project.seemproj -v  # MASW فقط
seem-geo corr --project project.seemproj  # Correlations
seem-geo fence --project project.seemproj  # Fence diagrams
seem-geo vs30-map --project project.seemproj # Vs30 map
seem-geo kmz --project project.seemproj  # KMZ export
seem-geo report --project project.seemproj  # PDF report
seem-geo pipeline --project project.seemproj # كل شيء
seem-geo picker --shot shot.csv  # Dispersion picker
seem-geo build-exe  # Windows .exe
```

---

## 🆘 حل المشاكل الشائعة

| المشكلة | الحل |
|---------|------|
| **`ModuleNotFoundError: No module named 'seem_geo'`** | `cd` لمجلد البرنامج و `pip install -e .` |
| **`tkinter` not found على Linux** | `sudo apt install python3-tk` |
| **MASW بطيء جداً** | قلّل `n_v` و `n_f` في المشروع (processing.masw_inversion) |
| **ERT inversion diverges** | قلّل `lambda_damping` من 10 إلى 5 |
| **Correlation builder مش لاقي بيانات** | تأكد إن أسماء الملفات: `ERT-NN_model.csv` و `MW-NN_vs_profile.csv` |
| **PDF report فشل** | matplotlib محتاج reinstall: `pip install --upgrade matplotlib` |

---

## 📞 الدعم

- **Email:** your-email@example.com
- **GitHub Issues:** https://github.com/ahmed/seem-geo/issues
- **Documentation:** `docs/` folder

---

*دليل الاستخدام — إصدار 1.1 — أكتوبر 2026*
