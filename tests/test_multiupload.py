"""Tests for multi-file operations: merge to PDF and batch conversion.

Covers:
- Core: DocumentConverter.merge_to_pdf (order, mixed formats, errors, progress)
- API: POST /api/merge (order, limits, dedupe, download)
- API: POST /api/batch (per-file results, partial failures, ZIP of all)

Per user request, this file does NOT cover docx2pdf/MS Word COM paths.
"""

import io
import json
import uuid
import zipfile
from pathlib import Path

import pytest
import fitz
from PIL import Image
from aiohttp.test_utils import TestClient, TestServer

from converter import ConversionOptions
from web_converter import app as app_module
from web_converter.app import create_app

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def pdf_alpha(test_dir):
    """2-page PDF with recognizable page markers."""
    path = test_dir / "alpha.pdf"
    doc = fitz.open()
    for marker in ("AlphaOne", "AlphaTwo"):
        page = doc.new_page()
        page.insert_text((72, 72), marker)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def pdf_bravo(test_dir):
    """1-page PDF with a recognizable marker."""
    path = test_dir / "bravo.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "BravoOne")
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def sample_png(test_dir):
    path = test_dir / "merge_img.png"
    Image.new('RGB', (100, 60), (30, 144, 255)).save(path)
    return path


@pytest.fixture
def note_txt(test_dir):
    path = test_dir / "note.txt"
    path.write_text("Test merge note content", encoding='utf-8')
    return path


@pytest.fixture
async def api_client():
    """Test client for a real application instance (with lifespan)."""
    app = await create_app()
    async with TestClient(TestServer(app)) as client:
        yield client


def _write_zero_page_pdf(path: Path):
    """Write a minimal valid PDF with zero pages.

    PyMuPDF refuses to SAVE documents with zero pages
    ("cannot save with zero pages"), so such a file has to be
    assembled by hand to test the defensive branch in merge.
    """
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[ ]/Count 0>>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj".encode() + obj + b"endobj\n"
    xref_pos = len(out)
    out += b"xref\n0 3\n0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<</Size 3/Root 1 0 R>>\nstartxref\n"
        + str(xref_pos).encode() + b"\n%%EOF"
    )
    path.write_bytes(out)


def _make_multipart(files, output_format=None, options=None, boundary=None):
    """Build multipart body with repeated 'files' fields (upload order kept)."""
    boundary = boundary or f'----Boundary{uuid.uuid4().hex[:12]}'
    body = b''
    for name, path in files:
        with open(path, 'rb') as f:
            data = f.read()
        body += (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="files"; filename="{name}"\r\n'
            f'Content-Type: application/octet-stream\r\n'
            f'\r\n'
        ).encode()
        body += data + b'\r\n'
    if output_format is not None:
        body += (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="output_format"\r\n'
            f'\r\n'
            f'{output_format}\r\n'
        ).encode()
    if options is not None:
        body += (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="options"\r\n'
            f'\r\n'
            f'{json.dumps(options)}\r\n'
        ).encode()
    body += f'--{boundary}--\r\n'.encode()
    return body, boundary


async def _post(client, body, boundary, endpoint):
    return await client.post(
        endpoint,
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    )


# ============================================================================
# Core: DocumentConverter.merge_to_pdf
# ============================================================================

class TestCoreMergeToPdf:

    def test_merge_two_pdfs_preserves_order(self, converter, pdf_alpha, pdf_bravo):
        result = converter.merge_to_pdf([str(pdf_alpha), str(pdf_bravo)])

        assert result.success is True
        assert result.output_path.endswith('.pdf')
        assert result.format == 'pdf'
        assert result.pages_processed == 3
        assert result.output_size > 0

        doc = fitz.open(result.output_path)
        try:
            assert doc.page_count == 3
            assert "AlphaOne" in doc[0].get_text()
            assert "AlphaTwo" in doc[1].get_text()
            assert "BravoOne" in doc[2].get_text()
        finally:
            doc.close()

    def test_merge_mixed_formats(self, converter, pdf_alpha, sample_png, note_txt):
        """PDF + image + text must all land in the merged PDF, in order."""
        result = converter.merge_to_pdf(
            [str(pdf_alpha), str(sample_png), str(note_txt)]
        )

        assert result.success is True
        assert result.pages_processed == 4  # 2 pdf pages + 1 image + 1 text page

        doc = fitz.open(result.output_path)
        try:
            assert "Test merge note content" in doc[3].get_text()
        finally:
            doc.close()

    def test_merge_unsupported_format_fails_with_filename(self, converter, pdf_alpha, test_dir):
        bad = test_dir / "data.xyz"
        bad.write_text("not convertible", encoding='utf-8')

        result = converter.merge_to_pdf([str(pdf_alpha), str(bad)])

        assert result.success is False
        assert "data.xyz" in result.error
        assert "xyz" in result.error

    def test_merge_empty_list(self, converter):
        result = converter.merge_to_pdf([])
        assert result.success is False
        assert "No files" in result.error

    def test_merge_all_empty_pdfs(self, converter, test_dir):
        empty = test_dir / "zero_pages.pdf"
        _write_zero_page_pdf(empty)

        result = converter.merge_to_pdf([str(empty), str(empty)])

        assert result.success is False
        assert "no pages" in result.error.lower()

    def test_merge_progress_callback(self, converter, pdf_alpha, sample_png, pdf_bravo):
        events = []
        result = converter.merge_to_pdf(
            [str(pdf_alpha), str(sample_png), str(pdf_bravo)],
            progress_callback=lambda done, total, msg: events.append((done, total, msg))
        )

        assert result.success is True
        assert len(events) >= 4  # one per file + final "concatenating"
        assert events[-1][0] == 3 and events[-1][1] == 3
        assert any("alpha.pdf" in msg for _, _, msg in events)
        assert any("bravo.pdf" in msg for _, _, msg in events)


# ============================================================================
# API: POST /api/merge
# ============================================================================

@pytest.mark.integration
class TestApiMerge:

    async def test_merge_two_pdfs_end_to_end(self, api_client, pdf_alpha, pdf_bravo):
        body, boundary = _make_multipart([("alpha.pdf", pdf_alpha), ("bravo.pdf", pdf_bravo)])

        resp = await _post(api_client, body, boundary, '/api/merge')
        assert resp.status == 200
        data = await resp.json()

        assert data['success'] is True
        assert data['format'] == 'pdf'
        assert data['merged_count'] == 2
        assert data['pages'] == 3
        assert data['download_url'].endswith('.pdf')

        dl = await api_client.get(data['download_url'])
        assert dl.status == 200
        content = await dl.read()

        doc = fitz.open(stream=content, filetype='pdf')
        try:
            assert doc.page_count == 3
            assert "AlphaOne" in doc[0].get_text()
            assert "BravoOne" in doc[2].get_text()
        finally:
            doc.close()

    async def test_merge_requires_at_least_two_files(self, api_client, pdf_alpha):
        body, boundary = _make_multipart([("alpha.pdf", pdf_alpha)])

        resp = await _post(api_client, body, boundary, '/api/merge')
        assert resp.status == 400
        data = await resp.json()
        assert data['success'] is False
        assert '2' in data['error']

    async def test_merge_rejects_unsupported_format(self, api_client, pdf_alpha, test_dir):
        bad = test_dir / "weird.xyz"
        bad.write_text("x", encoding='utf-8')

        body, boundary = _make_multipart(
            [("alpha.pdf", pdf_alpha), ("weird.xyz", bad)]
        )

        resp = await _post(api_client, body, boundary, '/api/merge')
        assert resp.status == 400
        data = await resp.json()
        assert data['success'] is False
        assert "xyz" in data['error']

    async def test_merge_duplicate_filenames_not_overwritten(
        self, api_client, pdf_alpha, pdf_bravo
    ):
        """Two different files both named doc.pdf must both be merged."""
        body, boundary = _make_multipart(
            [("doc.pdf", pdf_alpha), ("doc.pdf", pdf_bravo)]
        )

        resp = await _post(api_client, body, boundary, '/api/merge')
        assert resp.status == 200
        data = await resp.json()
        assert data['success'] is True
        assert data['pages'] == 3  # 2 + 1: second file did not overwrite the first

    async def test_merge_too_many_files_rejected(
        self, api_client, pdf_alpha, pdf_bravo, monkeypatch
    ):
        monkeypatch.setattr(app_module.config, 'max_files_per_request', 2)

        files = [("a.pdf", pdf_alpha), ("b.pdf", pdf_bravo), ("c.pdf", pdf_alpha)]
        body, boundary = _make_multipart(files)

        resp = await _post(api_client, body, boundary, '/api/merge')
        assert resp.status == 400
        data = await resp.json()
        assert data['success'] is False
        assert "Too many files" in data['error']


# ============================================================================
# API: POST /api/batch
# ============================================================================

@pytest.mark.integration
class TestApiBatch:

    async def test_batch_pdf_to_txt_with_zip(self, api_client, pdf_alpha, pdf_bravo):
        body, boundary = _make_multipart(
            [("alpha.pdf", pdf_alpha), ("bravo.pdf", pdf_bravo)],
            output_format='txt'
        )

        resp = await _post(api_client, body, boundary, '/api/batch')
        assert resp.status == 200
        data = await resp.json()

        assert data['success'] is True
        assert data['total'] == 2
        assert data['converted'] == 2
        assert data['failed'] == 0
        assert all(f['success'] for f in data['files'])

        urls = {f['download_url'] for f in data['files']}
        assert len(urls) == 2  # distinct outputs

        assert data['batch_zip_url'].endswith('.zip')
        dl = await api_client.get(data['batch_zip_url'])
        assert dl.status == 200
        content = await dl.read()
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = zf.namelist()
            assert len(names) == 2
            assert all(n.endswith('.txt') for n in names)

    async def test_batch_partial_failure(self, api_client, pdf_alpha, note_txt):
        """pdf->png works, txt->png is impossible: batch must partially succeed."""
        body, boundary = _make_multipart(
            [("alpha.pdf", pdf_alpha), ("note.txt", note_txt)],
            output_format='png'
        )

        resp = await _post(api_client, body, boundary, '/api/batch')
        assert resp.status == 200
        data = await resp.json()

        assert data['success'] is True
        assert data['converted'] == 1
        assert data['failed'] == 1

        by_name = {f['filename']: f for f in data['files']}
        assert by_name['alpha.pdf']['success'] is True
        assert by_name['note.txt']['success'] is False
        assert 'txt' in by_name['note.txt']['error']

        # Single successful output -> no pointless zip
        assert data['batch_zip_url'] is None

    async def test_batch_requires_output_format(self, api_client, pdf_alpha):
        body, boundary = _make_multipart([("alpha.pdf", pdf_alpha)])

        resp = await _post(api_client, body, boundary, '/api/batch')
        assert resp.status == 400
        data = await resp.json()
        assert data['success'] is False
        assert 'format' in data['error']
