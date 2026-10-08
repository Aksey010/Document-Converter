#!/usr/bin/env bash
# Document Converter - Unix launcher script
# Run with: ./run.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

print_banner() {
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ████████╗███████╗ █████╗ ██████╗ ███████╗██████╗  █████╗   ║
    ║   ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗  ║
    ║      ██║   █████╗  ███████║██████╔╝█████╗  ██████╔╝███████║  ║
    ║      ██║   ██╔══╝  ██╔══██║██╔══██╗██╔══╝  ██╔══██╗██╔══██║  ║
    ║      ██║   ███████╗██║  ██║██║  ██║███████╗██║  ██║██║  ██║  ║
    ║      ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝  ║
    ║                                                               ║
    ║   Document Converter — PDF, DOCX, TXT, HTML, DJVU, Images    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
}

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python not found. Install Python 3.9+"
        exit 1
    fi

    # Check version
    if ! $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        log_error "Python 3.9 or higher required. Found: $($PYTHON_CMD --version)"
        exit 1
    fi

    log_success "Python found: $($PYTHON_CMD --version)"
}

setup_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
        log_success "Virtual environment created"
    else
        log_info "Virtual environment found"
    fi

    # Upgrade pip
    log_info "Upgrading pip..."
    "$VENV_DIR/bin/python" -m pip install -q --upgrade pip
    log_success "pip upgraded"

    # Install dependencies
    log_info "Installing dependencies..."
    "$VENV_DIR/bin/python" -m pip install -q -r "$REQUIREMENTS"
    log_success "Dependencies installed"
}

check_system_tools() {
    # DJVU
    if command -v ddjvu &> /dev/null; then
        log_success "DJVU tools found: $(ddjvu --version 2>&1 | head -1)"
    else
        log_warn "djvulibre (ddjvu) not found. DJVU conversion unavailable."
        log_warn "Install: sudo apt install djvulibre-bin (Ubuntu/Debian) or brew install djvulibre (macOS)"
    fi

    # wkhtmltopdf
    if command -v wkhtmltopdf &> /dev/null; then
        log_success "wkhtmltopdf found: $(wkhtmltopdf --version 2>&1)"
    else
        log_warn "wkhtmltopdf not found. HTML→PDF will use fallback."
        log_warn "Install: sudo apt install wkhtmltopdf (Ubuntu/Debian) or brew install wkhtmltopdf (macOS)"
    fi

    # poppler (for pdf2image)
    if command -v pdftoppm &> /dev/null; then
        log_success "poppler found"
    else
        log_warn "poppler not found. PDF→image conversion may fail."
        log_warn "Install: sudo apt install poppler-utils (Ubuntu/Debian) or brew install poppler (macOS)"
    fi
}

main() {
    print_banner
    echo
    log_info "Starting Document Converter..."
    echo

    check_python
    setup_venv
    check_system_tools

    echo
    log_info "Starting web server..."
    echo -e "${GREEN}Panel will be available: http://localhost:8080${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo

    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        (sleep 3 && xdg-open http://localhost:8080) &
    elif command -v open &> /dev/null; then
        (sleep 3 && open http://localhost:8080) &
    fi

    # Run the app
    cd "$PROJECT_DIR"
    exec "$VENV_DIR/bin/python" main.py
}

main "$@"