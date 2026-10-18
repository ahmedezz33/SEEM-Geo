# نشر SEEM Geo على GitHub — خطوة بخطوة

**وقت متوقع:** 15 دقيقة · **مستوى:** مبتدئ

---

## 📋 الخطوات

### 1️⃣ إنشاء حساب GitHub

إذا ما عندك حساب:
1. روح على [github.com](https://github.com)
2. اضغط **Sign up**
3. استخدم ايميل الشركة: `your-email@example.com`
4. اختر Username زي `example-user` أو `example-user`

### 2️⃣ إنشاء Repository جديد

1. اضغط على **+** أعلى يمين الصفحة ثم **New repository**
2. املأ النموذج:
  - **Repository name:** `seem-geo`
  - **Description:** `Professional ERT & MASW Processing Suite — linear-infrastructure HVDC Thesis`
  - **Public** ✓ (أو Private لو تحب تخليه خاص)
  - **لا تختار** "Initialize this repository with a README" (عندنا README بالفعل)
3. اضغط **Create repository**

### 3️⃣ تثبيت Git على جهازك

#### Windows:
نزّل من [git-scm.com/download/win](https://git-scm.com/download/win) وثبّت بالإعدادات الافتراضية.

#### Mac:
```bash
brew install git
```

#### Linux:
```bash
sudo apt install git
```

### 4️⃣ إعداد Git (مرة واحدة فقط)

```bash
git config --global user.name "Ahmed"
git config --global user.email "your-email@example.com"
git config --global init.defaultBranch main
```

### 5️⃣ رفع البرنامج

افتح Terminal/CMD في مجلد `geophysics_suite_pro`:

```bash
cd path/to/geophysics_suite_pro

# ابدأ Git repository
git init

# أضف كل الملفات (ما عدا اللي في .gitignore)
git add .

# أول commit
git commit -m "feat: initial release — SEEM Geo v1.1.0"

# اربط بالـ GitHub repo (استبدل ahmedezz33 باسمك)
git remote add origin https://github.com/ahmedezz33/seem-geo.git

# ارفع
git branch -M main
git push -u origin main
```

في أول push هيطلبك اسم المستخدم وكلمة سر — استخدم:
- **Username:** اسم المستخدم
- **Password:** Personal Access Token (مش كلمة السر العادية)

### 6️⃣ إنشاء Personal Access Token

1. على GitHub: **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **Generate new token (classic)**
3. اختر:
  - **Note:** `SEEM Geo development`
  - **Expiration:** 90 days (أو No expiration)
  - **Scopes:** ✓ `repo` (كل الـ sub-items)
4. اضغط **Generate token**
5. **انسخ الـ token** (بيظهر مرة واحدة فقط!)
6. استخدمه كـ password عند الـ push

---

## 📦 إنشاء Release

لنشر الإصدار 1.1.0 رسمياً مع ملف الـ .exe:

### أ) من واجهة GitHub

1. على صفحة الـ repository → **Releases** (يمين) → **Create a new release**
2. املأ:
  - **Choose a tag:** `v1.1.0`
  - **Release title:** `SEEM Geo v1.1.0 — Full-featured`
  - **Description:** انسخ من `CHANGELOG.md`
3. ارفق `SEEM_Geo.exe` (لو بنيته)
4. اضغط **Publish release**

### ب) من Terminal (أسرع)

```bash
# أنشئ tag
git tag -a v1.1.0 -m "SEEM Geo v1.1.0 — Full-featured release"
git push origin v1.1.0
```

الـ CI workflow في `.github/workflows/ci.yml` هيبني الـ .exe تلقائياً ويرفعه كـ release asset.

---

## 🌟 جعل الـ Repository جذاب

### أ) إضافة Topics (كلمات مفتاحية للبحث)

على صفحة الـ repo → اضغط ⚙ بجانب **About** → **Topics** → أضف:
```
geophysics  ert  masw  wenner  resistivity  shear-wave  vs30
hvdc  engineering-geology  foundation-design
scipy  matplotlib  tkinter  python
```

### ب) إضافة Description واضح

في **About** section:
> Professional ERT (Wenner) & MASW processing suite with 2D inversion, Vs30 computation, local site classification, correlation framework, fence diagrams, KMZ export, and thesis-ready PDF reports.

### ج) إضافة Social Preview Image

**Settings** → **General** → **Social preview** → ارفع صورة 1280×640px (استخدم `docs/gui_preview.png` كمثال).

### د) تفعيل GitHub Pages (اختياري — للـ documentation)

**Settings** → **Pages** → **Source: `main` branch, `/docs` folder**
بعد كم دقيقة الدليل هيكون متاح على:
`https://ahmedezz33.github.io/seem-geo/USER_GUIDE_AR`

---

## 🔗 شارات README (Badges)

أضف هذي السطور في أعلى README.md عشان الـ repo يبان احترافي:

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![CI](https://github.com/ahmedezz33/seem-geo/actions/workflows/ci.yml/badge.svg)
![Version](https://img.shields.io/github/v/release/ahmedezz33/seem-geo)
![Downloads](https://img.shields.io/github/downloads/ahmedezz33/seem-geo/total)
![Issues](https://img.shields.io/github/issues/ahmedezz33/seem-geo)
![Stars](https://img.shields.io/github/stars/ahmedezz33/seem-geo)
```

---

## 📣 الترويج للـ Repository

### أ) على LinkedIn
انشر post على LinkedIn:

> أعلن عن إطلاق SEEM Geo — مكتبة Python مفتوحة المصدر لمعالجة بيانات
> ERT و MASW وإنتاج تقارير جاهزة للنشر، مبنية خلال رسالة الماجستير
> على مشروع خط الـ HVDC transmission-line لمشروع ممر HVDC.
>
> المميزات:
> ✓ معالجة ERT مع Occam inversion
> ✓ MASW + Vs30 + تصنيف applicable seismic design code
> ✓ Interactive dispersion picker
> ✓ Google Earth KMZ export
> ✓ تقرير PDF 58 صفحة جاهز للأطروحة
> ✓ ملف Windows .exe مستقل
>
> https://github.com/ahmedezz33/seem-geo
>
> #geophysics ##engineeringgeology #opensource

### ب) على ResearchGate
ارفع ورقة قصيرة (Preprint) تشرح البرنامج وتربطه بالـ repository.

### ج) اقترحه على زملائك
وزّعه على مجموعات WhatsApp/Telegram للمهندسين الجيوتقنيين في مجالك.

---

## 🧪 Zenodo DOI (للاستشهاد في الأبحاث)

لتحويل الـ repository لـ "citable software":

1. سجّل في [zenodo.org](https://zenodo.org) باستخدام GitHub
2. **GitHub** في Zenodo → فعّل الـ repository
3. أنشئ release جديد على GitHub (أو release موجود)
4. Zenodo تلقائياً هيعطيك **DOI** قابل للاستشهاد

يبقى في الورقة:
> *Ahmed. (2026). SEEM Geo: Professional ERT & MASW Processing Suite
> (Version 1.1.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.XXXXX*

---

## 🛡️ Security

لو عايز تحمي الـ repository من commits ضارة:

1. **Settings** → **Branches** → **Add rule** على `main`
2. فعّل:
  - ✓ Require pull request before merging
  - ✓ Require status checks (CI tests)
  - ✓ Require conversation resolution

---

## ✅ Checklist قبل أول push

- [ ] `README.md` محدَّث باسمك والإيميل الصحيح
- [ ] `LICENSE` موجود (MIT)
- [ ] `.gitignore` موجود (مش بيرفع __pycache__ و output/)
- [ ] `setup.py` فيه اسمك وبيئمتك
- [ ] `requirements.txt` موجود
- [ ] `CHANGELOG.md` فيه التغييرات
- [ ] `.github/workflows/ci.yml` للـ Continuous Integration
- [ ] ملفات Issue + PR templates
- [ ] `CONTRIBUTING.md` للمساهمين
- [ ] مش فيه بيانات شخصية أو إحداثيات حقلية حساسة في الـ examples

---

## 📞 لو احتجت مساعدة

- **GitHub Docs:** https://docs.github.com
- **Git Cheatsheet:** https://education.github.com/git-cheat-sheet-education.pdf
- **اسألني أي سؤال!**

---

*دليل النشر على GitHub — إصدار 1.0 — أكتوبر 2026*
