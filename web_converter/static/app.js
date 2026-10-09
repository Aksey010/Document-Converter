// Document Converter Frontend — Modern UI with Theme, Toasts, Keyboard Shortcuts

class DocumentConverter {
  constructor() {
    this.file = null;
    this.files = [];
    this.inputFormat = null;
    this.outputFormat = null;
    this.formats = [];
    this.compatibility = {};
    this.toastContainer = null;

    this.initElements();
    this.bindEvents();
    this.initTheme();
    this.initToasts();
    this.initKeyboardShortcuts();
    this.loadFormats();
  }

  initElements() {
    // Sections
    this.dropZone = document.getElementById('dropZone');
    this.fileInput = document.getElementById('fileInput');
    this.browseBtn = document.getElementById('browseBtn');
    this.fileInfo = document.getElementById('fileInfo');
    this.fileName = document.getElementById('fileName');
    this.fileSize = document.getElementById('fileSize');
    this.removeFileBtn = document.getElementById('removeFile');

    // Multi-file elements
    this.fileListWrap = document.getElementById('fileListWrap');
    this.fileList = document.getElementById('fileList');
    this.fileListCount = document.getElementById('fileListCount');
    this.fileListTotal = document.getElementById('fileListTotal');
    this.clearFilesBtn = document.getElementById('clearFilesBtn');
    this.mergeControls = document.getElementById('mergeControls');
    this.mergeToPdf = document.getElementById('mergeToPdf');
    this.noCommonFormat = document.getElementById('noCommonFormat');
    this.resultFiles = document.getElementById('resultFiles');

    // Cache the original drop zone content so it can be restored
    this._dropContentHtml = this.dropZone.querySelector('.drop-content').innerHTML;

    this.formatSection = document.getElementById('formatSection');
    this.formatGrid = document.getElementById('formatGrid');

    this.optionsSection = document.getElementById('optionsSection');
    this.quality = document.getElementById('quality');
    this.qualityValue = document.getElementById('qualityValue');
    this.dpi = document.getElementById('dpi');
    this.dpiValue = document.getElementById('dpiValue');
    this.resize = document.getElementById('resize');
    this.resizeValue = document.getElementById('resizeValue');
    this.pdfCompression = document.getElementById('pdfCompression');
    this.djvuQuality = document.getElementById('djvuQuality');
    this.djvuQualityValue = document.getElementById('djvuQualityValue');
    this.pageRange = document.getElementById('pageRange');
    this.grayscale = document.getElementById('grayscale');
    this.stripMetadata = document.getElementById('stripMetadata');
    this.estimateBox = document.getElementById('estimateBox');

    this.convertSection = document.getElementById('convertSection');
    this.convertBtn = document.getElementById('convertBtn');
    this.convertBtnText = this.convertBtn.querySelector('.btn-text');
    this.progress = document.getElementById('progress');
    this.progressBar = document.getElementById('progressBar');
    this.progressText = document.getElementById('progressText');

    this.resultSection = document.getElementById('resultSection');
    this.resultFormat = document.getElementById('resultFormat');
    this.resultInputSize = document.getElementById('resultInputSize');
    this.resultOutputSize = document.getElementById('resultOutputSize');
    this.resultRatio = document.getElementById('resultRatio');
    this.downloadBtn = document.getElementById('downloadBtn');
    this.convertAnotherBtn = document.getElementById('convertAnotherBtn');

    this.errorSection = document.getElementById('errorSection');
    this.errorMessage = document.getElementById('errorMessage');
    this.retryBtn = document.getElementById('retryBtn');

    this.downloadUrl = null;
  }

  bindEvents() {
    // File input
    this.browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.fileInput.click();
    });

    this.fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) this.addFiles(e.target.files);
    });

    // Drag and drop
    this.dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      this.dropZone.classList.add('drag-over');
    });

    this.dropZone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      this.dropZone.classList.remove('drag-over');
    });

    this.dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      this.dropZone.classList.remove('drag-over');
      if (e.dataTransfer.files.length) this.addFiles(e.dataTransfer.files);
    });

    this.dropZone.addEventListener('click', () => this.fileInput.click());
    this.dropZone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.fileInput.click();
      }
    });

    this.removeFileBtn.addEventListener('click', () => this.resetFile());
    this.clearFilesBtn.addEventListener('click', () => this.resetFile());

    // Merge toggle (multi-file mode)
    this.mergeToPdf.addEventListener('change', () => {
      if (this.files.length >= 2) this.refreshFileUI();
    });

    // Option changes -> update estimate
    const optionInputs = [
      this.quality, this.dpi, this.resize, this.pdfCompression,
      this.djvuQuality, this.pageRange, this.grayscale, this.stripMetadata
    ];
    optionInputs.forEach(el => el?.addEventListener('input', () => this.updateEstimate()));

    this.quality.addEventListener('input', () => this.qualityValue.textContent = this.quality.value);
    this.dpi.addEventListener('input', () => this.dpiValue.textContent = this.dpi.value);
    this.resize.addEventListener('input', () => this.resizeValue.textContent = parseFloat(this.resize.value).toFixed(1));
    this.djvuQuality.addEventListener('input', () => this.djvuQualityValue.textContent = this.djvuQuality.value);

    // Convert
    this.convertBtn.addEventListener('click', () => this.convert());

    // Download
    this.downloadBtn.addEventListener('click', () => this.download());

    // Convert another
    this.convertAnotherBtn.addEventListener('click', () => this.resetAll());

    // Retry
    this.retryBtn.addEventListener('click', () => this.hideError());
  }

  // --- Theme Management ---
  initTheme() {
    const toggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // Get saved theme or detect system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');

    html.setAttribute('data-theme', theme);

    toggle?.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      this.showToast('success', `Тема: ${next === 'dark' ? 'тёмная' : 'светлая'}`);
    });

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      }
    });
  }

  // --- Toast Notifications ---
  initToasts() {
    this.toastContainer = document.getElementById('toastContainer');
  }

  showToast(type, message, duration = 4000) {
    if (!this.toastContainer) return;

    const icons = {
      success: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
      error: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
      warning: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
      info: '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-message">${this.escapeHtml(message)}</span>
      <button class="toast-close" aria-label="Закрыть"><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => this.removeToast(toast));

    this.toastContainer.appendChild(toast);

    // Auto-remove
    setTimeout(() => this.removeToast(toast), duration);
  }

  removeToast(toast) {
    if (!toast.parentElement) return;
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }

  // --- Keyboard Shortcuts ---
  initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + O = Open file
      if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        this.fileInput.click();
      }
      // Enter = Convert (when convert section visible and not disabled)
      if (e.key === 'Enter' && !this.convertBtn.disabled &&
          !this.convertSection.classList.contains('hidden') &&
          document.activeElement !== this.pageRange) {
        e.preventDefault();
        this.convert();
      }
      // Escape = Clear files / close error
      if (e.key === 'Escape') {
        if (!this.errorSection.classList.contains('hidden')) {
          this.hideError();
        } else if (this.files.length) {
          this.resetFile();
        }
      }
      // Ctrl/Cmd + Shift + T = Toggle theme
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        document.getElementById('themeToggle')?.click();
      }
    });
  }

  // --- Format Loading ---
  async loadFormats() {
    try {
      const response = await fetch('/api/formats');
      const data = await response.json();
      this.formats = data.input_formats;
      this.compatibility = data.compatibility;
    } catch (e) {
      console.error('Failed to load formats:', e);
      this.showToast('error', 'Не удалось загрузить поддерживаемые форматы');
    }
  }

  // --- File Handling (multi-file) ---
  addFiles(fileList) {
    const incoming = Array.from(fileList);
    let added = 0;

    incoming.forEach(f => {
      const ext = f.name.split('.').pop().toLowerCase();
      if (!this.formats.includes(ext)) {
        this.showToast('error', `Неподдерживаемый формат: ${f.name}`);
        return;
      }
      this.files.push(f);
      added++;
    });

    // Reset input so the same file(s) can be picked again later
    this.fileInput.value = '';

    if (added) {
      this.showToast('success', added === 1
        ? `Файл добавлен (всего: ${this.files.length})`
        : `Добавлено файлов: ${added} (всего: ${this.files.length})`);
    }
    this.refreshFileUI();
  }

  refreshFileUI() {
    const n = this.files.length;

    if (n === 0) {
      this.file = null;
      this.inputFormat = null;
      this.outputFormat = null;
      this._restoreDropContent();
      this.dropZone.classList.remove('has-file');
      this.fileListWrap.classList.add('hidden');
      this.fileInfo.classList.add('hidden');
      this.mergeControls.classList.add('hidden');
      this.noCommonFormat.classList.add('hidden');
      this.hideAllSections();
      this.convertBtn.disabled = true;
      this.convertBtnText.textContent = 'Конвертировать';
      this.downloadBtn.classList.remove('hidden');
      this.resultFiles.classList.add('hidden');
      this.resultFiles.innerHTML = '';
      this.estimateBox.classList.add('hidden');
      return;
    }

    if (n === 1) {
      this.file = this.files[0];
      this.inputFormat = this.file.name.split('.').pop().toLowerCase();
      this.fileListWrap.classList.add('hidden');
      this.mergeControls.classList.add('hidden');
      this.noCommonFormat.classList.add('hidden');
      this._renderSingleFileUI();
      this.renderFormats();
      this.formatSection.classList.remove('hidden');
      this.optionsSection.classList.remove('hidden');
      this.convertBtnText.textContent = 'Конвертировать';
      this.showPreliminaryEstimate();
      return;
    }

    // Multi-file mode (2+)
    this.file = null;
    this.inputFormat = null;
    this.outputFormat = null;
    this._restoreDropContent();
    this.dropZone.classList.remove('has-file');
    this.fileInfo.classList.add('hidden');

    this.renderFileList();
    this.fileListWrap.classList.remove('hidden');
    this.renderMultiFormats();
    this.formatSection.classList.remove('hidden');
    this.estimateBox.classList.add('hidden');
  }

  _restoreDropContent() {
    const dropContent = this.dropZone.querySelector('.drop-content');
    dropContent.innerHTML = this._dropContentHtml;
    // Re-bind browse button (innerHTML replaced the node)
    this.browseBtn = dropContent.querySelector('#browseBtn');
    this.browseBtn?.addEventListener('click', (e) => {
      e.stopPropagation();
      this.fileInput.click();
    });
  }

  _renderSingleFileUI() {
    const file = this.file;
    this.dropZone.classList.add('has-file');

    const dropContent = this.dropZone.querySelector('.drop-content');
    dropContent.innerHTML = `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <p class="drop-title">Файл готов к конвертации</p>
      <p class="drop-subtitle">${this.escapeHtml(file.name)} <span class="file-size-badge">${this.formatSize(file.size)}</span></p>
      <p class="hint">Выберите формат вывода ниже</p>
      <button type="button" class="btn-change-file" aria-label="Выбрать другой файл">Выбрать другой файл</button>
    `;

    dropContent.querySelector('.btn-change-file').addEventListener('click', (e) => {
      e.stopPropagation();
      this.resetFile();
    });

    this.fileInfo.classList.add('hidden');
  }

  renderFileList() {
    const totalSize = this.files.reduce((s, f) => s + f.size, 0);
    this.fileListCount.textContent = `Файлов: ${this.files.length}`;
    this.fileListTotal.textContent = this.formatSize(totalSize);

    this.fileList.innerHTML = this.files.map((f, i) => `
      <li class="file-row" data-index="${i}">
        <span class="file-index">${i + 1}</span>
        <span class="file-row-name" title="${this.escapeHtml(f.name)}">${this.escapeHtml(f.name)}</span>
        <span class="file-row-size">${this.formatSize(f.size)}</span>
        <span class="file-row-actions">
          <button type="button" class="row-btn" data-action="up" data-index="${i}" aria-label="Переместить выше" ${i === 0 ? 'disabled' : ''}>↑</button>
          <button type="button" class="row-btn" data-action="down" data-index="${i}" aria-label="Переместить ниже" ${i === this.files.length - 1 ? 'disabled' : ''}>↓</button>
          <button type="button" class="row-btn row-remove" data-action="remove" data-index="${i}" aria-label="Удалить из списка">×</button>
        </span>
      </li>
    `).join('');

    this.fileList.querySelectorAll('.row-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const i = parseInt(btn.dataset.index, 10);
        const action = btn.dataset.action;
        if (action === 'up' && i > 0) {
          [this.files[i - 1], this.files[i]] = [this.files[i], this.files[i - 1]];
        } else if (action === 'down' && i < this.files.length - 1) {
          [this.files[i + 1], this.files[i]] = [this.files[i], this.files[i + 1]];
        } else if (action === 'remove') {
          this.files.splice(i, 1);
        }
        this.refreshFileUI();
      });
    });
  }

  computeCommonFormats() {
    let common = null;
    for (const f of this.files) {
      const ext = f.name.split('.').pop().toLowerCase();
      const outputs = this.compatibility[ext] || [];
      common = common === null ? [...outputs] : common.filter(x => outputs.includes(x));
      if (common.length === 0) break;
    }
    return common || [];
  }

  allMergeable() {
    return this.files.length >= 2 && this.files.every(f => {
      const ext = f.name.split('.').pop().toLowerCase();
      return (this.compatibility[ext] || []).includes('pdf');
    });
  }

  pluralFiles(n) {
    const mod10 = n % 10;
    const mod100 = n % 100;
    if (mod10 === 1 && mod100 !== 11) return 'файл';
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'файла';
    return 'файлов';
  }

  renderMultiFormats() {
    const common = this.computeCommonFormats();
    const mergeable = this.allMergeable();
    const mergeOn = mergeable && this.mergeToPdf.checked;

    this.mergeControls.classList.toggle('hidden', !mergeable);
    this.noCommonFormat.classList.toggle('hidden', common.length > 0 || mergeOn);

    if (mergeOn) {
      // Merge mode: output is always a single PDF
      this.outputFormat = 'pdf';
      this.formatGrid.innerHTML = '';
      this.optionsSection.classList.remove('hidden');
      this.convertSection.classList.remove('hidden');
      this.convertBtn.disabled = false;
      this.convertBtnText.textContent = `Объединить ${this.files.length} ${this.pluralFiles(this.files.length)} в PDF`;
      this.updateOptionsVisibility();
      this.estimateBox.classList.add('hidden');
      return;
    }

    if (common.length === 0) {
      this.outputFormat = null;
      this.formatGrid.innerHTML = '';
      this.convertSection.classList.add('hidden');
      this.convertBtn.disabled = true;
      this.convertBtnText.textContent = 'Конвертировать';
      return;
    }

    // Batch mode: common output formats for all files
    this.renderFormatsList(common);
    this.convertBtnText.textContent = `Конвертировать ${this.files.length} ${this.pluralFiles(this.files.length)}`;
  }

  // Show preliminary estimate right after file upload (before format selection)
  async showPreliminaryEstimate() {
    if (!this.file || this.files.length !== 1) return;
    
    const outputFormats = this.compatibility[this.inputFormat] || [];
    if (outputFormats.length === 0) return;

    // Use first available format for preliminary estimate
    const preliminaryFormat = outputFormats[0];
    const options = this.getOptions();

    try {
      const response = await fetch('/api/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: this.file.name,
          output_format: preliminaryFormat,
          options
        })
      });

      const data = await response.json();

      if (!data.error) {
        document.getElementById('estimateInputSize').textContent = this.formatSize(data.input_size);
        document.getElementById('estimateOutputSize').textContent = this.formatSize(data.estimated_output_size);
        document.getElementById('estimateRatio').textContent = data.compression_ratio + 'x';
        this.estimateBox.classList.remove('hidden');
        
        // Add a label to indicate this is preliminary
        const estimateLabel = this.estimateBox.querySelector('h3');
        if (estimateLabel && !estimateLabel.dataset.original) {
          estimateLabel.dataset.original = estimateLabel.textContent;
          estimateLabel.textContent = `📊 Прогноз размера (в ${preliminaryFormat.toUpperCase()})`;
        }
      }
    } catch (e) {
      console.error('Preliminary estimate failed:', e);
    }
  }

  renderFormats() {
    this.renderFormatsList(this.compatibility[this.inputFormat] || []);
  }

  renderFormatsList(outputFormats) {
    // Format icons (inline SVG)
    const icons = {
      pdf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><text x="8" y="16" font-size="6" fill="currentColor">PDF</text></svg>',
      docx: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><text x="8" y="16" font-size="6" fill="currentColor">DOCX</text></svg>',
      txt: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><text x="8" y="16" font-size="6" fill="currentColor">TXT</text></svg>',
      html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><text x="8" y="16" font-size="6" fill="currentColor">HTML</text></svg>',
      png: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/></svg>',
      jpeg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/></svg>',
      tiff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/></svg>',
      bmp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/></svg>',
      webp: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/></svg>',
      gif: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-5-5L5 21"/></svg>',
      djvu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><text x="8" y="16" font-size="6" fill="currentColor">DJVU</text></svg>'
    };

    const labels = {
      pdf: 'PDF', docx: 'DOCX', txt: 'TXT', html: 'HTML',
      png: 'PNG', jpeg: 'JPEG', jpg: 'JPG', tiff: 'TIFF',
      bmp: 'BMP', webp: 'WEBP', gif: 'GIF', djvu: 'DJVU', djv: 'DJV'
    };

    this.formatGrid.innerHTML = outputFormats.map(fmt => `
      <button type="button" class="format-btn${fmt === outputFormats[0] ? ' selected' : ''}"
              data-format="${fmt}" role="radio" aria-checked="${fmt === outputFormats[0]}"
              aria-label="${labels[fmt] || fmt.toUpperCase()}">
        <span class="icon">${icons[fmt] || '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>'}</span>
        <span>${labels[fmt] || fmt.toUpperCase()}</span>
      </button>
    `).join('');

    // Select first by default
    this.outputFormat = outputFormats[0];

    // Bind format buttons
    this.formatGrid.querySelectorAll('.format-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.formatGrid.querySelectorAll('.format-btn').forEach(b => {
          b.classList.remove('selected');
          b.setAttribute('aria-checked', 'false');
        });
        btn.classList.add('selected');
        btn.setAttribute('aria-checked', 'true');
        this.outputFormat = btn.dataset.format;
        this.updateOptionsVisibility();
        this.updateEstimate();
        this.convertSection.classList.remove('hidden');
        this.convertBtn.disabled = false;
      });

      // Keyboard support for format buttons
      btn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          btn.click();
        }
      });
    });

    this.updateOptionsVisibility();
    this.convertSection.classList.remove('hidden');
    this.convertBtn.disabled = false;
  }

  updateOptionsVisibility() {
    const isImage = ['png', 'jpeg', 'jpg', 'tiff', 'bmp', 'webp', 'gif'].includes(this.outputFormat);
    const isPdf = this.outputFormat === 'pdf';
    const isDjvu = ['djvu', 'djv'].includes(this.outputFormat);

    const toggles = {
      quality: isImage || isDjvu,
      dpi: isImage || isPdf || isDjvu,
      resize: isImage,
      pdfCompression: isPdf,
      djvuQuality: isDjvu,
      pageRange: ['pdf', 'djvu', 'djv', 'tiff'].includes(this.outputFormat) || ['pdf', 'djvu', 'djv'].includes(this.inputFormat),
      grayscale: isImage,
      stripMetadata: isImage || isPdf
    };

    Object.entries(toggles).forEach(([id, show]) => {
      const el = document.getElementById(id);
      if (el) {
        const group = el.closest('.option-group');
        if (group) group.style.display = show ? 'flex' : 'none';
      }
    });
  }

  // --- Estimation ---
  async updateEstimate() {
    if (!this.file || !this.outputFormat || this.files.length !== 1) {
      this.estimateBox.classList.add('hidden');
      return;
    }

    const options = this.getOptions();

    try {
      const response = await fetch('/api/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: this.file.name,
          output_format: this.outputFormat,
          options
        })
      });

      const data = await response.json();

      if (data.error) {
        this.estimateBox.classList.add('hidden');
        return;
      }

      document.getElementById('estimateInputSize').textContent = this.formatSize(data.input_size);
      document.getElementById('estimateOutputSize').textContent = this.formatSize(data.estimated_output_size);
      document.getElementById('estimateRatio').textContent = data.compression_ratio + 'x';

      // Update label to show selected format
      const estimateLabel = this.estimateBox.querySelector('h3');
      if (estimateLabel && estimateLabel.dataset.original) {
        estimateLabel.textContent = estimateLabel.dataset.original;
      }

      this.estimateBox.classList.remove('hidden');
    } catch (e) {
      console.error('Estimate failed:', e);
      this.estimateBox.classList.add('hidden');
    }
  }

  getOptions() {
    return {
      quality: parseInt(this.quality.value),
      dpi: parseInt(this.dpi.value),
      pdf_compression: this.pdfCompression.value,
      resize_factor: parseFloat(this.resize.value),
      djvu_quality: parseInt(this.djvuQuality.value),
      page_range: this.pageRange.value || null,
      grayscale: this.grayscale.checked,
      strip_metadata: this.stripMetadata.checked
    };
  }

  // --- Conversion ---
  async convert() {
    // Multi-file mode: merge to PDF or batch conversion
    if (this.files.length >= 2) {
      if (this.allMergeable() && this.mergeToPdf.checked) {
        return this.convertMerge();
      }
      return this.convertBatch();
    }

    if (!this.file || !this.outputFormat) return;

    this.hideAllSections();
    this.progress.classList.remove('hidden');
    this.progress.classList.add('indeterminate');
    this.convertBtn.disabled = true;
    this.convertBtn.classList.add('loading');
    this.progressText.textContent = 'Загрузка файла...';
    this.progressBar.style.width = '0%';

    const formData = new FormData();
    formData.append('file', this.file);
    formData.append('output_format', this.outputFormat);
    formData.append('options', JSON.stringify(this.getOptions()));

    try {
      this.progressText.textContent = 'Загрузка файла...';

      // Step 1: Upload file and get task_id
      const taskId = await this.uploadFile(formData);
      if (!taskId) return;

      // Step 2: Connect to SSE for real-time progress
      await this.trackProgress(taskId);

    } catch (e) {
      this.progress.classList.add('hidden');
      this.progress.classList.remove('indeterminate');
      this.convertBtn.classList.remove('loading');
      this.convertBtn.disabled = false;
      this.showError('Ошибка сети: ' + e.message);
      this.showToast('error', 'Ошибка сети: ' + e.message);
    }
  }

  // Multi-file: merge all files into one PDF
  async convertMerge() {
    const formData = new FormData();
    this.files.forEach(f => formData.append('files', f, f.name));
    formData.append('options', JSON.stringify(this.getOptions()));
    return this.runOperation(formData, '/api/merge');
  }

  // Multi-file: convert each file independently
  async convertBatch() {
    if (!this.outputFormat) {
      this.showToast('warning', 'Нет общего формата вывода для всех файлов');
      return;
    }

    const formData = new FormData();
    this.files.forEach(f => formData.append('files', f, f.name));
    formData.append('output_format', this.outputFormat);
    formData.append('options', JSON.stringify(this.getOptions()));
    return this.runOperation(formData, '/api/batch');
  }

  // Shared upload + SSE progress flow for merge/batch operations
  async runOperation(formData, endpoint) {
    this.hideAllSections();
    this.progress.classList.remove('hidden');
    this.progress.classList.add('indeterminate');
    this.convertBtn.disabled = true;
    this.convertBtn.classList.add('loading');
    this.progressText.textContent = 'Загрузка файлов...';
    this.progressBar.style.width = '0%';

    try {
      const taskId = await this.uploadFile(formData, endpoint);
      if (!taskId) return;
      await this.trackProgress(taskId);
    } catch (e) {
      this.progress.classList.add('hidden');
      this.progress.classList.remove('indeterminate');
      this.convertBtn.classList.remove('loading');
      this.convertBtn.disabled = false;
      this.showError('Ошибка сети: ' + e.message);
      this.showToast('error', 'Ошибка сети: ' + e.message);
    }
  }

  // Upload files and get task_id
  uploadFile(formData, endpoint = '/api/convert') {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          this.progressBar.style.width = percent + '%';
          this.progressText.textContent = `Загрузка: ${percent}%`;
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            this.progress.classList.remove('indeterminate');
            
            if (data.success && data.task_id) {
              resolve(data.task_id);
            } else {
              this.progress.classList.add('hidden');
              this.convertBtn.classList.remove('loading');
              this.convertBtn.disabled = false;
              
              if (data.error) {
                this.showError(data.error);
                this.showToast('error', data.error);
              } else {
                this.showError('Ошибка конвертации');
                this.showToast('error', 'Ошибка конвертации');
              }
              reject(new Error(data.error || 'Conversion failed'));
            }
          } catch (e) {
            reject(new Error('Неверный ответ сервера'));
          }
        } else {
          reject(new Error(`Ошибка сервера: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Ошибка сети')));
      xhr.addEventListener('abort', () => reject(new Error('Прервано')));

      xhr.open('POST', endpoint);
      xhr.send(formData);
    });
  }

  // Track progress via SSE
  async trackProgress(taskId) {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(`/api/convert/progress/${taskId}`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          this.progressBar.style.width = data.progress + '%';
          this.progressText.textContent = data.message;
          
          if (data.status === 'completed') {
            eventSource.close();
            this.progress.classList.add('hidden');
            this.progress.classList.remove('indeterminate');
            this.convertBtn.classList.remove('loading');
            
            if (data.result) {
              this.showResult(data.result);
              this.showToast('success', 'Конвертация завершена успешно!');
            } else {
              this.showError(data.error || 'Ошибка конвертации');
              this.showToast('error', data.error || 'Ошибка конвертации');
            }
            resolve();
          } else if (data.status === 'error') {
            eventSource.close();
            this.progress.classList.add('hidden');
            this.progress.classList.remove('indeterminate');
            this.convertBtn.classList.remove('loading');
            this.convertBtn.disabled = false;
            this.showError(data.error || 'Ошибка конвертации');
            this.showToast('error', data.error || 'Ошибка конвертации');
            reject(new Error(data.error || 'Conversion failed'));
          }
        } catch (e) {
          console.error('SSE parse error:', e);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        this.progress.classList.add('hidden');
        this.progress.classList.remove('indeterminate');
        this.convertBtn.classList.remove('loading');
        this.convertBtn.disabled = false;
        this.showError('Соединение с сервером прервано');
        this.showToast('error', 'Соединение с сервером прервано');
        reject(new Error('SSE connection lost'));
      };
    });
  }

  showResult(data) {
    this.resultSection.classList.remove('hidden');
    this.resultFiles.innerHTML = '';
    this.resultFiles.classList.add('hidden');
    this.downloadBtn.classList.remove('hidden');
    this.downloadUrl = null;

    if (data.files) {
      // Batch conversion result: per-file links + optional ZIP of all
      this.resultFormat.textContent = `${(data.format || '').toUpperCase()} × ${data.converted}`;
      this.resultInputSize.textContent = `${data.total} ${this.pluralFiles(data.total)}`;
      this.resultOutputSize.textContent = `успешно: ${data.converted}, с ошибками: ${data.failed}`;
      this.resultRatio.textContent = '—';
      this.downloadBtn.classList.add('hidden');

      const rows = data.files.map(r => r.success
        ? `<li class="result-file success">
             <a href="${r.download_url}" download>${this.escapeHtml(r.filename)}</a>
             <span class="result-file-size">${this.formatSize(r.output_size)}</span>
           </li>`
        : `<li class="result-file failed">
             <span>${this.escapeHtml(r.filename)}</span>
             <span class="result-error">${this.escapeHtml(r.error || 'Ошибка')}</span>
           </li>`
      ).join('');

      const zipRow = data.batch_zip_url
        ? `<li class="result-file zip"><a href="${data.batch_zip_url}" download>📦 Скачать все успешные (${data.converted}) одним архивом ZIP</a></li>`
        : '';

      this.resultFiles.innerHTML = `<ul class="result-files-list">${rows}${zipRow}</ul>`;
      this.resultFiles.classList.remove('hidden');
      return;
    }

    if (data.merged_count) {
      // Merge result: single merged PDF
      this.resultFormat.textContent = 'PDF (объединённый)';
      this.resultInputSize.textContent = this.formatSize(data.input_size);
      this.resultOutputSize.textContent = this.formatSize(data.output_size);
      this.resultRatio.textContent = `${data.pages} стр. из ${data.merged_count} ${this.pluralFiles(data.merged_count)}`;
      this.downloadUrl = data.download_url;
      return;
    }

    // Single-file result
    this.resultFormat.textContent = data.format.toUpperCase();
    this.resultInputSize.textContent = this.formatSize(data.input_size);
    this.resultOutputSize.textContent = this.formatSize(data.output_size);
    this.resultRatio.textContent = data.compression_ratio + 'x';

    this.downloadUrl = data.download_url;
  }

  download() {
    if (this.downloadUrl) {
      window.location.href = this.downloadUrl;
      this.showToast('info', 'Скачивание начато');
    }
  }

  showError(message) {
    this.hideAllSections();
    this.errorSection.classList.remove('hidden');
    this.errorMessage.textContent = message;
  }

  hideError() {
    this.errorSection.classList.add('hidden');
  }

  hideAllSections() {
    this.formatSection.classList.add('hidden');
    this.optionsSection.classList.add('hidden');
    this.convertSection.classList.add('hidden');
    this.resultSection.classList.add('hidden');
    this.errorSection.classList.add('hidden');
    this.progress.classList.add('hidden');
  }

  // --- Reset ---
  resetFile() {
    this.file = null;
    this.files = [];
    this.inputFormat = null;
    this.outputFormat = null;
    this.fileInput.value = '';
    this.dropZone.classList.remove('has-file');
    this._restoreDropContent();
    this.dropZone.querySelector('.drop-content').style.display = '';
    this.fileInfo.classList.add('hidden');
    this.fileListWrap.classList.add('hidden');
    this.mergeControls.classList.add('hidden');
    this.noCommonFormat.classList.add('hidden');
    this.resultFiles.classList.add('hidden');
    this.resultFiles.innerHTML = '';
    this.downloadBtn.classList.remove('hidden');
    this.mergeToPdf.checked = true;
    this.hideAllSections();
    this.convertBtn.disabled = true;
    this.convertBtnText.textContent = 'Конвертировать';
    this.estimateBox.classList.add('hidden');
  }

  resetAll() {
    this.resetFile();
    // Reset options to defaults
    this.quality.value = 85;
    this.qualityValue.textContent = 85;
    this.dpi.value = 150;
    this.dpiValue.textContent = 150;
    this.resize.value = 1;
    this.resizeValue.textContent = '1.0';
    this.pdfCompression.value = 'medium';
    this.djvuQuality.value = 50;
    this.djvuQualityValue.textContent = 50;
    this.pageRange.value = '';
    this.grayscale.checked = false;
    this.stripMetadata.checked = true;
    this.showToast('info', 'Форма сброшена');
  }

  // --- Utilities ---
  formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.converter = new DocumentConverter();
});

// Service Worker registration for PWA (optional)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js').catch(() => {
      // SW optional, ignore errors
    });
  });
}