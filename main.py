#!/usr/bin/env python3
"""
Document Converter - Main entry point for web application.

Run with: python main.py
Or use start_converter.bat (Windows) / ./run.sh (Unix) for automatic setup.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from web_converter.app import main

def print_banner():
    """Print startup banner."""
    # Use ASCII-only banner for Windows console compatibility
    banner = r"""
    ====================================================================
    |                                                                  |
    |   Document Converter — PDF, DOCX, TXT, HTML, DJVU, Images       |
    |                                                                  |
    ====================================================================
    """
    print(banner)

if __name__ == '__main__':
    print_banner()
    print("Starting Document Converter web panel...")
    print("Panel will be available: http://localhost:8080")
    print("Press Ctrl+C to stop\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nShutdown complete. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)