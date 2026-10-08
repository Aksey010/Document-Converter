"""Web application for Document Converter - Optimized version."""

import asyncio
import os
import sys
import tempfile
import shutil
import time
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import json
import uuid

from aiohttp import web
from aiohttp.web import Request, Response, FileResponse
import aiohttp_jinja2
import jinja2

from converter import DocumentConverter, ConversionOptions, OutputFormat, InputFormat

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class AppConfig:
    """Application configuration."""
    # Server
    host: str = "localhost"
    port: int = 8080
    
    # File limits
    max_file_size: int = 100 * 1024 * 1024  # 100 MB
    max_concurrent_conversions: int = 2  # Limit concurrent conversions
    
    # Timeouts
    conversion_timeout: int = 300  # 5 minutes per conversion
    upload_timeout: int = 60  # 1 minute for upload
    
    # Temp file management
    temp_dir_prefix: str = "doc_converter"
    temp_file_ttl: int = 3600  # 1 hour TTL for temp files
    cleanup_interval: int = 300  # Cleanup every 5 minutes
    
    # Thread pool
    thread_pool_workers: int = 2
    
    def __post_init__(self):
        # Validate config
        if self.max_concurrent_conversions < 1:
            self.max_concurrent_conversions = 1
        if self.thread_pool_workers < 1:
            self.thread_pool_workers = 1


# Global configuration
config = AppConfig()

# ============================================================================
# Temp File Manager with TTL Cleanup
# ============================================================================

class TempFileManager:
    """Manages temporary files with automatic TTL-based cleanup."""
    
    def __init__(self, prefix: str = "doc_converter", ttl: int = 3600):
        self.prefix = prefix
        self.ttl = ttl
        self.upload_dir = Path(tempfile.gettempdir()) / f"{prefix}_uploads"
        self.output_dir = Path(tempfile.gettempdir()) / f"{prefix}_output"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self, interval: int = 300):
        """Start periodic cleanup task."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop(interval))
        logger.info(f"Temp file manager started (TTL: {self.ttl}s, interval: {interval}s)")
    
    async def stop(self):
        """Stop cleanup task and do final cleanup."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.cleanup_all()
        logger.info("Temp file manager stopped")
    
    async def _cleanup_loop(self, interval: int):
        """Periodic cleanup loop."""
        while self._running:
            try:
                await asyncio.sleep(interval)
                if self._running:
                    await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def cleanup_expired(self):
        """Remove expired temp files."""
        now = time.time()
        removed = 0
        
        for dir_path in (self.upload_dir, self.output_dir):
            if not dir_path.exists():
                continue
            for file_path in dir_path.iterdir():
                try:
                    if file_path.is_file():
                        mtime = file_path.stat().st_mtime
                        if now - mtime > self.ttl:
                            file_path.unlink()
                            removed += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup {file_path}: {e}")
        
        if removed:
            logger.info(f"Cleaned up {removed} expired temp files")
    
    async def cleanup_all(self):
        """Remove all temp files (on shutdown)."""
        removed = 0
        for dir_path in (self.upload_dir, self.output_dir):
            if not dir_path.exists():
                continue
            for file_path in dir_path.iterdir():
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        removed += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup {file_path}: {e}")
        if removed:
            logger.info(f"Cleaned up all {removed} temp files on shutdown")


# ============================================================================
# Global Instances
# ============================================================================

# Global converter instance
converter = DocumentConverter()

# Temp file manager
temp_manager = TempFileManager(prefix=config.temp_dir_prefix, ttl=config.temp_file_ttl)

# Concurrency control
conversion_semaphore = asyncio.Semaphore(config.max_concurrent_conversions)

# Thread pool executor
from concurrent.futures import ThreadPoolExecutor
thread_pool = ThreadPoolExecutor(max_workers=config.thread_pool_workers)

# ============================================================================
# Progress Tracking
# ============================================================================

from dataclasses import dataclass
from typing import Dict, Optional
import uuid

@dataclass
class ConversionTask:
    """Track conversion progress."""
    task_id: str
    filename: str
    output_format: str
    status: str = "pending"  # pending, uploading, converting, completed, error
    progress: float = 0.0
    message: str = "Waiting..."
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)

# Global task store
task_store: Dict[str, ConversionTask] = {}

def create_task(filename: str, output_format: str) -> ConversionTask:
    """Create a new conversion task."""
    task_id = str(uuid.uuid4())[:8]
    task = ConversionTask(
        task_id=task_id,
        filename=filename,
        output_format=output_format,
        status="pending",
        progress=0.0,
        message="Initializing..."
    )
    task_store[task_id] = task
    return task

def update_task_progress(task_id: str, progress: float, message: str, status: str = None):
    """Update task progress."""
    if task_id in task_store:
        task = task_store[task_id]
        task.progress = max(0.0, min(100.0, progress))
        task.message = message
        if status:
            task.status = status

def complete_task(task_id: str, result: dict = None, error: str = None):
    """Mark task as completed."""
    if task_id in task_store:
        task = task_store[task_id]
        if error:
            task.status = "error"
            task.error = error
            task.message = f"Error: {error}"
        else:
            task.status = "completed"
            task.progress = 100.0
            task.message = "Completed successfully"
            task.result = result

def get_task(task_id: str) -> Optional[ConversionTask]:
    """Get task by ID."""
    return task_store.get(task_id)

def cleanup_old_tasks(max_age: int = 3600):
    """Remove old completed tasks."""
    now = time.time()
    to_remove = [
        task_id for task_id, task in task_store.items()
        if task.status in ("completed", "error") and now - task.created_at > max_age
    ]
    for task_id in to_remove:
        del task_store[task_id]

# ============================================================================
# Routes
# ============================================================================

def setup_routes(app: web.Application):
    """Setup application routes."""
    app.router.add_get('/', index_handler)
    app.router.add_get('/api/formats', formats_handler)
    app.router.add_post('/api/convert', convert_handler)
    app.router.add_get('/api/convert/progress/{task_id}', progress_sse_handler)
    app.router.add_post('/api/estimate', estimate_handler)
    app.router.add_get('/download/{filename}', download_handler)
    app.router.add_get('/api/status', status_handler)
    app.router.add_static('/static/', Path(__file__).parent / 'static')


# ============================================================================
# Handlers
# ============================================================================

async def index_handler(request: Request) -> Response:
    """Serve the main page."""
    return FileResponse(Path(__file__).parent / 'templates' / 'index.html')


async def formats_handler(request: Request) -> Response:
    """Get supported formats."""
    input_formats = converter.get_supported_input_formats()
    
    # Build compatibility matrix
    compatibility = {}
    for fmt in input_formats:
        compatibility[fmt] = converter.get_supported_output_formats(fmt)
    
    return web.json_response({
        "input_formats": input_formats,
        "output_formats": [f.value for f in OutputFormat],
        "compatibility": compatibility
    })


async def status_handler(request: Request) -> Response:
    """Get server status."""
    from converter.libraries import get_libraries
    libs = get_libraries()
    lib_status = libs.get_status()
    
    return web.json_response({
        "status": "ok",
        "conversions_active": config.max_concurrent_conversions - conversion_semaphore._value,
        "conversions_max": config.max_concurrent_conversions,
        "thread_pool_workers": config.thread_pool_workers,
        "temp_dirs": {
            "uploads": str(temp_manager.upload_dir),
            "output": str(temp_manager.output_dir),
        },
        "libraries": lib_status,
    })


async def progress_sse_handler(request: Request) -> Response:
    """SSE endpoint for conversion progress updates."""
    task_id = request.match_info['task_id']
    task = get_task(task_id)
    
    if not task:
        return web.json_response({"error": "Task not found"}, status=404)
    
    # Create SSE response
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )
    await response.prepare(request)
    
    try:
        # Send initial state
        await _send_sse_event(response, task)
        
        # Stream updates until completion
        while task.status in ("pending", "uploading", "converting"):
            await asyncio.sleep(0.5)
            if task.status in ("completed", "error"):
                await _send_sse_event(response, task)
                break
            else:
                await _send_sse_event(response, task)
        
        # Final event
        await _send_sse_event(response, task)
        
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"SSE error for task {task_id}: {e}")
    finally:
        await response.write_eof()
    
    return response


async def _send_sse_event(response: web.StreamResponse, task: ConversionTask):
    """Send SSE event with task data."""
    import json
    data = {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "result": task.result,
        "error": task.error
    }
    await response.write(f"data: {json.dumps(data)}\n\n".encode())


async def convert_handler(request: Request) -> Response:
    """Handle file conversion with streaming upload."""
    # Check concurrency limit
    if conversion_semaphore.locked():
        return web.json_response({
            "error": "Server busy: maximum concurrent conversions reached. Please try again later."
        }, status=503, headers={"Retry-After": "30"})
    
    async with conversion_semaphore:
        return await _convert_with_semaphore(request)


async def _convert_with_semaphore(request: Request) -> Response:
    """Internal conversion handler with semaphore already acquired."""
    temp_input_path = None
    
    try:
        # Check content length
        content_length = request.headers.get('Content-Length')
        if content_length and int(content_length) > config.max_file_size:
            return web.json_response({
                "error": f"File too large. Maximum size: {config.max_file_size // (1024*1024)} MB"
            }, status=413)
        
        # Stream upload directly to temp file
        reader = await request.multipart()
        
        file_field = None
        output_format = None
        options_data = {}
        file_filename = None
        file_size = 0
        
        # Process multipart fields
        async for field in reader:
            if field.name == 'file':
                file_filename = field.filename
                if not file_filename:
                    return web.json_response({"error": "No file selected"}, status=400)
                
                # Validate extension early
                input_ext = Path(file_filename).suffix.lower().lstrip('.')
                if input_ext not in converter.get_supported_input_formats():
                    return web.json_response(
                        {"error": f"Unsupported input format: {input_ext}"},
                        status=400
                    )
                
                # Stream directly to temp file
                temp_input_path = temp_manager.upload_dir / file_filename
                file_size = 0
                
                with open(temp_input_path, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk(8192)
                        if not chunk:
                            break
                        file_size += len(chunk)
                        if file_size > config.max_file_size:
                            f.close()
                            temp_input_path.unlink(missing_ok=True)
                            return web.json_response({
                                "error": f"File too large. Maximum: {config.max_file_size // (1024*1024)} MB"
                            }, status=413)
                        f.write(chunk)
                
            elif field.name == 'output_format':
                output_format = await field.text()
            elif field.name == 'options':
                options_data = json.loads(await field.text())
        
        if not file_filename:
            return web.json_response({"error": "No file uploaded"}, status=400)
        
        if not output_format:
            return web.json_response({"error": "No output format specified"}, status=400)
        
        # Validate conversion
        input_ext = Path(file_filename).suffix.lower().lstrip('.')
        if not converter.can_convert(input_ext, output_format):
            temp_input_path.unlink(missing_ok=True)
            return web.json_response(
                {"error": f"Cannot convert {input_ext} to {output_format}"},
                status=400
            )
        
        # Parse options
        options = ConversionOptions(
            quality=options_data.get('quality', 85),
            dpi=options_data.get('dpi', 150),
            pdf_compression=options_data.get('pdf_compression', 'medium'),
            resize_factor=options_data.get('resize_factor', 1.0),
            djvu_quality=options_data.get('djvu_quality', 50),
            page_range=options_data.get('page_range'),
            grayscale=options_data.get('grayscale', False),
            strip_metadata=options_data.get('strip_metadata', True),
            output_dir=str(temp_manager.output_dir),
        )
        
        # Create task for progress tracking
        task = create_task(file_filename, output_format)
        task_id = task.task_id
        
        # Update progress: upload complete
        update_task_progress(task_id, 10.0, "File uploaded, starting conversion...", "converting")
        
        # Parse options
        options = ConversionOptions(
            quality=options_data.get('quality', 85),
            dpi=options_data.get('dpi', 150),
            pdf_compression=options_data.get('pdf_compression', 'medium'),
            resize_factor=options_data.get('resize_factor', 1.0),
            djvu_quality=options_data.get('djvu_quality', 50),
            page_range=options_data.get('page_range'),
            grayscale=options_data.get('grayscale', False),
            strip_metadata=options_data.get('strip_metadata', True),
            output_dir=str(temp_manager.output_dir),
        )
        
        # Run conversion in thread pool with timeout
        loop = asyncio.get_event_loop()
        try:
            # Update progress during conversion
            update_task_progress(task_id, 30.0, "Converting document...", "converting")
            
            # Run conversion with progress updates
            def conversion_with_progress():
                # Update progress periodically
                update_task_progress(task_id, 50.0, "Processing document...")
                result = converter.convert(str(temp_input_path), output_format, options)
                update_task_progress(task_id, 90.0, "Finalizing...")
                return result
            
            result = await asyncio.wait_for(
                loop.run_in_executor(thread_pool, conversion_with_progress),
                timeout=config.conversion_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Conversion timeout for {file_filename} -> {output_format}")
            complete_task(task_id, error=f"Conversion timed out ({config.conversion_timeout}s limit)")
            return web.json_response({
                "error": f"Conversion timed out ({config.conversion_timeout}s limit)",
                "task_id": task_id
            }, status=504)
        
        # Clean up input file
        if temp_input_path:
            temp_input_path.unlink(missing_ok=True)
        
        if result.success:
            complete_task(task_id, {
                "filename": Path(result.output_path).name,
                "output_size": result.output_size,
                "input_size": result.input_size,
                "compression_ratio": round(result.output_size / result.input_size, 2) if result.input_size > 0 else 0,
                "format": result.format,
                "download_url": f"/download/{Path(result.output_path).name}"
            })
            return web.json_response({
                "success": True,
                "task_id": task_id,
                "filename": Path(result.output_path).name,
                "output_size": result.output_size,
                "input_size": result.input_size,
                "compression_ratio": round(result.output_size / result.input_size, 2) if result.input_size > 0 else 0,
                "format": result.format,
                "download_url": f"/download/{Path(result.output_path).name}"
            })
        else:
            complete_task(task_id, error=result.error)
            return web.json_response({
                "success": False,
                "error": result.error,
                "task_id": task_id
            }, status=500)
            
    except asyncio.CancelledError:
        # Client disconnected
        if temp_input_path:
            temp_input_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        logger.exception(f"Conversion error: {e}")
        if temp_input_path:
            temp_input_path.unlink(missing_ok=True)
        if 'task_id' in locals():
            complete_task(task_id, error=str(e))
        return web.json_response({"error": str(e)}, status=500)


async def estimate_handler(request: Request) -> Response:
    """Estimate output file size."""
    try:
        data = await request.json()
        input_filename = data.get('filename')
        output_format = data.get('output_format')
        options_data = data.get('options', {})
        
        if not input_filename or not output_format:
            return web.json_response({"error": "Missing filename or output_format"}, status=400)
        
        # Find the uploaded file
        input_path = temp_manager.upload_dir / input_filename
        if not input_path.exists():
            return web.json_response({"error": "File not found"}, status=404)
        
        options = ConversionOptions(
            quality=options_data.get('quality', 85),
            dpi=options_data.get('dpi', 150),
            pdf_compression=options_data.get('pdf_compression', 'medium'),
            resize_factor=options_data.get('resize_factor', 1.0),
            djvu_quality=options_data.get('djvu_quality', 50),
            grayscale=options_data.get('grayscale', False),
        )
        
        # Use improved estimation
        estimate = await _improved_estimate(input_path, output_format, options)
        return web.json_response(estimate)
        
    except Exception as e:
        logger.exception(f"Estimate error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def download_handler(request: Request) -> Response:
    """Download converted file."""
    filename = request.match_info['filename']
    # Prevent path traversal
    filename = Path(filename).name
    file_path = temp_manager.output_dir / filename
    
    if not file_path.exists():
        return web.json_response({"error": "File not found"}, status=404)
    
    return FileResponse(file_path, headers={
        'Content-Disposition': f'attachment; filename="{filename}"'
    })


# ============================================================================
# Improved Size Estimation
# ============================================================================

async def _improved_estimate(input_path: Path, output_format: str, options: ConversionOptions) -> dict:
    """Improved size estimation using format-aware heuristics."""
    input_size = input_path.stat().st_size
    input_format = input_path.suffix.lower().lstrip('.')
    output_format = output_format.lower()
    
    # Format-specific estimation factors (derived from empirical data)
    # These are rough but more accurate than simple multipliers
    
    # Base factors per output format
    format_factors = {
        'pdf': {
            'pdf': 0.8,  # PDF -> PDF (compression)
            'docx': 0.3,  # DOCX -> PDF
            'txt': 0.15,  # TXT -> PDF
            'html': 0.4,  # HTML -> PDF
            'default': 0.5,  # Images -> PDF
        },
        'docx': {
            'pdf': 1.5,
            'docx': 1.0,
            'txt': 2.0,
            'html': 1.8,
            'default': 2.5,
        },
        'txt': {
            'pdf': 5.0,  # Text expands with formatting
            'docx': 10.0,
            'html': 3.0,
        },
        'html': {
            'pdf': 2.0,
            'docx': 3.0,
            'txt': 0.2,
            'default': 1.5,
        },
        'png': {
            'pdf': 1.2,
            'docx': 2.0,
            'png': 1.0,
            'jpeg': 0.3,
            'tiff': 2.5,
            'bmp': 8.0,
            'webp': 0.4,
        },
        'jpeg': {
            'pdf': 1.2,
            'docx': 2.0,
            'png': 3.0,
            'jpeg': 1.0,
            'tiff': 2.5,
            'bmp': 8.0,
            'webp': 0.4,
        },
        'tiff': {
            'pdf': 1.0,
            'png': 0.5,
            'jpeg': 0.2,
            'tiff': 1.0,
            'bmp': 4.0,
            'webp': 0.3,
        },
        'bmp': {
            'pdf': 0.5,
            'png': 0.1,
            'jpeg': 0.05,
            'tiff': 0.3,
            'bmp': 1.0,
            'webp': 0.05,
        },
        'webp': {
            'pdf': 1.2,
            'png': 1.5,
            'jpeg': 0.5,
            'tiff': 2.0,
            'bmp': 6.0,
            'webp': 1.0,
        },
        'gif': {
            'pdf': 1.5,
            'png': 2.0,
            'jpeg': 0.5,
            'tiff': 3.0,
            'bmp': 8.0,
            'webp': 0.5,
        },
    }
    
    # Get format-specific factor
    format_map = format_factors.get(input_format, {})
    base_factor = format_map.get(output_format, format_map.get('default', 1.0))
    
    # Adjust for options
    dpi_factor = (options.dpi / 150) ** 2
    quality_factor = options.quality / 85
    resize_factor = options.resize_factor ** 2
    grayscale_factor = 0.4 if options.grayscale else 1.0
    
    # Format-specific option sensitivity
    if output_format in ('jpeg', 'jpg', 'webp'):
        estimated = int(input_size * base_factor * quality_factor * resize_factor * grayscale_factor)
    elif output_format in ('png', 'tiff', 'bmp'):
        estimated = int(input_size * base_factor * dpi_factor * resize_factor * grayscale_factor)
    elif output_format == 'pdf':
        if input_format in ('png', 'jpeg', 'jpg', 'tiff', 'bmp', 'webp', 'gif'):
            estimated = int(input_size * base_factor * dpi_factor * resize_factor * grayscale_factor)
        else:
            estimated = int(input_size * base_factor * quality_factor)
    else:
        estimated = int(input_size * base_factor * dpi_factor * quality_factor)
    
    # Clamp to reasonable bounds
    estimated = max(100, min(estimated, input_size * 20))
    
    return {
        "input_size": input_size,
        "estimated_output_size": estimated,
        "compression_ratio": round(estimated / input_size, 2) if input_size > 0 else 0,
        "options": {
            "quality": options.quality,
            "dpi": options.dpi,
            "resize_factor": options.resize_factor,
            "grayscale": options.grayscale,
        },
        "factors": {
            "base_factor": base_factor,
            "dpi_factor": round(dpi_factor, 2),
            "quality_factor": round(quality_factor, 2),
            "resize_factor": round(resize_factor, 2),
            "grayscale_factor": grayscale_factor,
        }
    }


# ============================================================================
# Application Lifecycle
# ============================================================================

async def app_lifespan(app: web.Application):
    """Application lifespan manager (async generator for aiohttp cleanup_ctx)."""
    # Startup
    logger.info("Starting Document Converter...")
    logger.info(f"Config: max_file_size={config.max_file_size/1024/1024}MB, "
                f"max_concurrent={config.max_concurrent_conversions}, "
                f"timeout={config.conversion_timeout}s, "
                f"thread_pool={config.thread_pool_workers}")
    
    # Start temp file manager
    await temp_manager.start(interval=config.cleanup_interval)
    
    # Pre-warm libraries
    try:
        from converter.libraries import get_libraries
        libs = get_libraries()
        libs.get_status()
        logger.info("Libraries pre-warmed")
    except Exception as e:
        logger.warning(f"Library pre-warm failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Document Converter...")
    
    # Wait for active conversions to finish (with timeout)
    shutdown_timeout = 30
    start = time.time()
    while conversion_semaphore.locked():
        if time.time() - start > shutdown_timeout:
            logger.warning("Shutdown timeout reached, forcing exit")
            break
        await asyncio.sleep(0.5)
    
    # Shutdown thread pool
    thread_pool.shutdown(wait=True, cancel_futures=True)
    
    # Stop temp file manager
    await temp_manager.stop()
    
    logger.info("Shutdown complete")


async def create_app() -> web.Application:
    """Create and configure the web application."""
    app = web.Application()
    
    # Setup lifespan
    app.cleanup_ctx.append(app_lifespan)
    
    # Setup Jinja2
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(str(Path(__file__).parent / 'templates'))
    )
    
    setup_routes(app)
    return app


async def main():
    """Run the web server."""
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.host, config.port)
    await site.start()
    print(f"Document Converter web panel: http://{config.host}:{config.port}")
    
    # Keep running
    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)