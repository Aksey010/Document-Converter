"""Tests for multi-page PDF -> images conversion with ZIP packaging.

Feature: converting a PDF to image formats renders ALL pages (not just the
first one). When more than one output file is produced, the result is
delivered as a ZIP archive containing one image file per page.

Per user request, this file intentionally does NOT cover the items that
could not be covered so far (docx2pdf/MS Word COM dependent tests and
tests/test_pdf_txt.py).
"""

import io
import uuid
import zipfile
from pathlib import Path

import pytest
import fitz
from PIL import Image
from aiohttp.test_utils import TestClient, TestServer

from converter import DocumentConverter, ConversionOptions
from web_converter.app import create_app

# Distinct page sizes (points) so per-page rendering can be verified
PAGE_SIZES = [(200, 400), (300, 300), (400, 200)]


@pytest.fixture
def multipage_pdf(test_dir):
    """Create a 3-page PDF with pages of distinct sizes."""
    pdf_path = test_dir / "multipage_sample.pdf"
    doc = fitz.open()
    for i, (w, h) in enumerate(PAGE_SIZES, start=1):
        page = doc.new_page(width=w, height=h)
        page.insert_text((20, 30), f"Page {i}")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def _make_multipart(file_path: Path, output_format: str, boundary: str) -> bytes:
    """Build a multipart/form-data body (file + output_format fields)."""
    with open(file_path, 'rb') as f:
        file_data = f.read()

    parts = [
        f'--{boundary}',
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"',
        'Content-Type: application/octet-stream',
        '',
    ]
    body = '\r\n'.join(parts).encode() + b'\r\n' + file_data + b'\r\n'
    body += f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="output_format"\r\n\r\n'
    body += output_format.encode() + b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    return body


# ============================================================================
# Handler-level tests
# ============================================================================

class TestPDFMultiPageToImages:
    """PDFHandler converts every page; multi-page results become ZIPs."""

    def test_all_pages_rendered_into_zip(self, pdf_handler, multipage_pdf, test_dir):
        """3-page PDF -> PNG must produce a ZIP with one image per page."""
        output = test_dir / "mp.png"
        result = pdf_handler.convert(
            str(multipage_pdf), str(output), 'png',
            ConversionOptions(dpi=72)
        )

        assert result == str(test_dir / "mp.zip")
        assert Path(result).exists()
        assert zipfile.is_zipfile(result)

        with zipfile.ZipFile(result) as zf:
            assert zf.namelist() == [f"mp_page_{i:03d}.png" for i in (1, 2, 3)]
            for i, (w, h) in enumerate(PAGE_SIZES, start=1):
                with Image.open(io.BytesIO(zf.read(f"mp_page_{i:03d}.png"))) as img:
                    assert img.format == 'PNG'
                    assert abs(img.width - w) <= 2, f"page {i}: {img.size}"
                    assert abs(img.height - h) <= 2, f"page {i}: {img.size}"

    def test_single_page_stays_plain_file(self, pdf_handler, sample_text_pdf, test_dir):
        """1-page PDF -> PNG must stay a plain image file (no archive)."""
        output = test_dir / "plain.png"
        result = pdf_handler.convert(
            str(sample_text_pdf), str(output), 'png', ConversionOptions()
        )

        assert result == str(output)
        assert Path(output).exists()
        assert not zipfile.is_zipfile(output)
        with Image.open(output) as img:
            assert img.format == 'PNG'

    def test_page_range_zip_contains_only_selected_pages(self, pdf_handler, multipage_pdf, test_dir):
        """page_range='2-3' must yield a ZIP with pages 2 and 3 only."""
        output = test_dir / "pr.png"
        result = pdf_handler.convert(
            str(multipage_pdf), str(output), 'png',
            ConversionOptions(page_range="2-3", dpi=72)
        )

        assert zipfile.is_zipfile(result)
        with zipfile.ZipFile(result) as zf:
            assert zf.namelist() == ["pr_page_002.png", "pr_page_003.png"]

    @pytest.mark.parametrize("fmt", ["jpeg", "tiff", "bmp", "webp"])
    def test_multipage_other_image_formats(self, pdf_handler, multipage_pdf, test_dir, fmt):
        """Every image output format must package all pages into a ZIP."""
        output = test_dir / f"mpf.{fmt}"
        result = pdf_handler.convert(
            str(multipage_pdf), str(output), fmt, ConversionOptions(dpi=72)
        )

        assert zipfile.is_zipfile(result)
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert len(names) == 3
            assert all(name.endswith(f".{fmt}") for name in names)


# ============================================================================
# Core-level tests
# ============================================================================

class TestCoreMultiPageConversion:
    """DocumentConverter returns the ZIP as a successful conversion result."""

    def test_convert_multipage_pdf_returns_zip(self, converter, multipage_pdf):
        result = converter.convert(str(multipage_pdf), 'png', ConversionOptions(dpi=72))

        assert result.success is True
        assert result.output_path.endswith('.zip')
        assert result.format == 'png'
        assert result.output_size > 0
        assert zipfile.is_zipfile(result.output_path)
        with zipfile.ZipFile(result.output_path) as zf:
            assert len(zf.namelist()) == 3


# ============================================================================
# API-level (integration) tests
# ============================================================================

@pytest.fixture
async def api_client():
    """Test client for a real application instance (with lifespan)."""
    app = await create_app()
    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.mark.integration
class TestAPIMultiPageZipDownload:
    """Full stack: upload multi-page PDF, download ZIP with all pages."""

    async def test_multipage_pdf_downloads_as_zip(self, api_client, multipage_pdf):
        boundary = f'----Boundary{uuid.uuid4().hex[:12]}'
        body = _make_multipart(multipage_pdf, 'png', boundary)

        resp = await api_client.post(
            '/api/convert',
            data=body,
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data['success'] is True
        assert data['format'] == 'png'
        assert data['download_url'].endswith('.zip')

        dl = await api_client.get(data['download_url'])
        assert dl.status == 200
        content = await dl.read()
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            assert zf.namelist() == [
                "multipage_sample_page_001.png",
                "multipage_sample_page_002.png",
                "multipage_sample_page_003.png",
            ]
