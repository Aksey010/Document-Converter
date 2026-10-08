# 📄 Document Converter

> A beautiful, modern web-based document converter supporting **PDF, DOCX, TXT, HTML, DJVU, and images** with real-time preview, size estimation, and batch processing.

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-orange)]()

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔄 **Multi-format** | PDF ↔ DOCX ↔ TXT ↔ HTML ↔ Images (PNG, JPEG, TIFF, BMP, WEBP, GIF) + DJVU |
| 🎨 **Modern UI** | Drag & drop, real-time format compatibility, live size estimation |
| ⚙️ **Smart Options** | Quality, DPI, resize, compression, grayscale, metadata stripping, page ranges |
| 📊 **Size Preview** | Instant output size estimation before conversion |
| 🚀 **Fast & Local** | Runs entirely on your machine — no cloud uploads |
| 🌙 **Dark Mode** | Automatic system theme detection + manual toggle |
| 📱 **Responsive** | Works on desktop, tablet, and mobile |
| ♿ **Accessible** | WCAG 2.1 AA compliant, keyboard navigation, screen reader support |

---

## 🎯 Supported Conversions

```
Input → Output Formats
─────────────────────
PDF        → PDF, DOCX, TXT, HTML, PNG, JPEG, TIFF, BMP, WEBP
DOCX       → PDF, TXT, HTML, PNG, JPEG
TXT        → PDF, DOCX, HTML
HTML       → PDF, DOCX, TXT, PNG, JPEG
DJVU/DJV   → PDF, PNG, JPEG, TIFF, TXT
Images     → PDF, DOCX, PNG, JPEG, TIFF, BMP, WEBP
```

> **Note**: DJVU requires [`djvulibre`](https://djvu.sourceforge.net/) (`ddjvu` in PATH). HTML→PDF needs [`wkhtmltopdf`](https://wkhtmltopdf.org/) for best results.

---

## 🚀 Quick Start

### Windows (Easiest)
```bat
# Just double-click or run in terminal:
start_converter.bat
```
✅ Auto-creates virtual environment  
✅ Installs all dependencies  
✅ Opens browser at `http://localhost:8080`

### Manual (Any OS)
```bash
# 1. Clone & enter
git clone https://github.com/yourusername/document-converter.git
cd document-converter

# 2. Create venv & install
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Run
python main.py
# Open http://localhost:8080
```

### Docker (Coming Soon)
```bash
docker run -p 8080:8080 document-converter
```

---

## 🎮 Usage

1. **Drop a file** or click to browse
2. **Pick output format** — only compatible formats shown
3. **Tune options** (quality, DPI, pages, etc.) — see live size estimate
4. **Click Convert** → **Download** result

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `Ctrl/Cmd + O` | Open file dialog |
| `Enter` | Convert (when ready) |
| `Escape` | Clear file / close dialog |
| `Tab` | Navigate UI |

---

## 🏗️ Architecture

```
document-converter/
├── main.py                 # Entry point
├── requirements.txt        # Python deps
├── start_converter.bat     # Windows launcher
├── converter/              # Core conversion engine
│   ├── core.py             # DocumentConverter, formats, options
│   └── formats/            # Format handlers
│       ├── base.py         # BaseHandler interface
│       ├── pdf_handler.py  # PyMuPDF + pdf2image
│       ├── docx_handler.py # python-docx + docx2pdf
│       ├── txt_handler.py  # Text processing
│       ├── html_handler.py # BeautifulSoup + html2docx + wkhtmltopdf
│       ├── image_handler.py# Pillow + PyMuPDF
│       └── djvu_handler.py # ddjvu CLI wrapper
├── web_converter/          # Web UI (aiohttp + Jinja2)
│   ├── app.py              # Server + API routes
│   ├── templates/index.html
│   └── static/
│       ├── app.js          # Frontend logic
│       └── style.css       # Modern responsive CSS
└── tests/                  # (Add your tests here)
```

---

## ⚙️ Configuration

### Environment Variables
```bash
# Optional: custom ports/dirs
export CONVERTER_HOST=0.0.0.0
export CONVERTER_PORT=8080
export CONVERTER_UPLOAD_DIR=/tmp/uploads
export CONVERTER_OUTPUT_DIR=/tmp/output
```

### Conversion Options (API)
```json
{
  "quality": 85,           // 1-100 (JPEG/WEBP/DJVU)
  "dpi": 150,              // 72-600 (rasterization)
  "pdf_compression": "medium",  // low|medium|high
  "resize_factor": 1.0,    // 0.1-3.0
  "djvu_quality": 50,      // 0-100
  "page_range": "1-5",     // "1,3,5" or "1-5"
  "grayscale": false,
  "strip_metadata": true
}
```

---

## 🛠️ Development

### Run with Auto-reload
```bash
# Install dev deps
pip install watchdog

# Run with file watching
python -m watchdog.run --patterns="*.py;*.html;*.css;*.js" -- python main.py
```

### Code Style
```bash
pip install ruff black isort
ruff check .
black .
isort .
```

### Type Checking
```bash
pip install mypy
mypy converter/ web_converter/
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `aiohttp`, `aiohttp-jinja2`, `jinja2` | Async web server + templating |
| `pymupdf` (fitz) | PDF read/write/rasterize |
| `pdf2image` + `poppler` | PDF → images |
| `python-docx`, `docx2pdf` | DOCX read/write |
| `Pillow` | Image processing |
| `beautifulsoup4`, `html2docx` | HTML parsing + conversion |
| `mammoth` | DOCX → HTML |
| `pytesseract` | OCR (optional) |
| `orjson` | Fast JSON |

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feat/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feat/amazing-feature`
5. Open a Pull Request

### Ideas for Contributions
- [ ] Batch conversion UI
- [ ] OCR integration (Tesseract)
- [ ] PDF merge/split/rotate
- [ ] File compression presets
- [ ] WebP/AVIF support
- [ ] Unit/integration tests
- [ ] CI/CD pipeline

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [PyMuPDF](https://pymupdf.readthedocs.io/) — Incredible PDF library
- [Pillow](https://pillow.readthedocs.io/) — Friendly PIL fork
- [pdf2image](https://github.com/Belval/pdf2image) — PDF to images
- [aiohttp](https://aiohttp.readthedocs.io/) — Async HTTP
- [Lucide Icons](https://lucide.dev/) — Beautiful SVG icons (inline)

---

<div align="center">
  <strong>Made with ❤️ for document freedom</strong>
  <br>
  <sub>Star ⭐ if this helped you!</sub>
</div>