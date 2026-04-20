"""LuminaLog Python SDK - Main Logger Implementation"""

import atexit
import json
import threading
import time
import traceback
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import requests

from .types import LogLevel, LogEntry, LogBatch, ErrorPayload, IngestionResponse

DEFAULT_ENDPOINT = "https://api-dev.luminalog.cloud/v1/logs"
DEFAULT_BATCH_SIZE = 100
MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 500
DEFAULT_FLUSH_INTERVAL = 5.0


def generate_trace_id() -> str:
    """Generate a new trace ID (UUID v4)"""
    return str(uuid.uuid4())


def generate_span_id() -> str:
    """Generate a new span ID (UUID v4)"""
    return str(uuid.uuid4())


def get_trace_id_from_request(request: Any) -> str:
    """
    Extract trace ID from common request headers.
    Checks x-trace-id, x-request-id, traceparent (W3C format).
    
    Args:
        request: Request object (Flask, FastAPI, Django, etc.)
    
    Returns:
        Trace ID string
    """
    if hasattr(request, 'headers'):
        headers = request.headers
        
        trace_id = headers.get('x-trace-id') or headers.get('x-request-id')
        if trace_id:
            return trace_id
        
        traceparent = headers.get('traceparent')
        if traceparent:
            parts = traceparent.split('-')
            if len(parts) >= 2:
                return parts[1]
    
    return generate_trace_id()


class LuminaLog:
    """
    LuminaLog SDK for Python
    
    Privacy-first logging with AI-powered debugging.
    Automatically batches logs and flushes periodically.
    """

    def __init__(
        self,
        api_key: str,
        environment: str = "default",
        project_id: Optional[str] = None,
        privacy_mode: bool = False,
        min_level: Optional[LogLevel] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        flush_interval: float = DEFAULT_FLUSH_INTERVAL,
        endpoint: str = DEFAULT_ENDPOINT,
        debug: bool = False,
    ):
        """
        Initialize LuminaLog SDK
        
        Args:
            api_key: Your LuminaLog API key (required)
            environment: Label for filtering logs (stored as metadata). 
                        The actual environment is determined by your API key's 
                        environment setting in the dashboard.
            project_id: Optional project identifier
            privacy_mode: Enable privacy mode to scrub sensitive data (default: False)
            min_level: Minimum log level to send (default: None, sends all levels)
            batch_size: Number of logs before auto-flush (default: 100)
            flush_interval: Seconds between auto-flushes (default: 5.0)
            endpoint: API endpoint URL (default: LuminaLog cloud)
            debug: Enable debug logging (default: False)
        """
        if not api_key:
            raise ValueError("LuminaLog: api_key is required")

        self.api_key = api_key
        self.environment = environment
        self.project_id = project_id
        self.privacy_mode = privacy_mode
        self.min_level = min_level
        
        if batch_size < MIN_BATCH_SIZE:
            print(
                f"[LuminaLog] Warning: batch_size must be at least 1. Using 1 instead."
            )
            self.batch_size = MIN_BATCH_SIZE
        elif batch_size > MAX_BATCH_SIZE:
            print(
                f"[LuminaLog] Warning: batch_size {batch_size} exceeds maximum {MAX_BATCH_SIZE}. "
                f"Using {MAX_BATCH_SIZE} instead."
            )
            self.batch_size = MAX_BATCH_SIZE
        else:
            self.batch_size = batch_size
        
        self.flush_interval = flush_interval
        self.endpoint = endpoint
        self.debug_mode = debug
        self._base_metadata: Dict[str, Any] = {}

        self._queue: List[LogEntry] = []
        self._queue_lock = threading.Lock()
        self._is_flushing = False
        self._flush_timer: Optional[threading.Timer] = None
        self._shutdown = False
        
        self._log_levels = ["debug", "info", "warn", "error", "fatal", "panic"]

        self._start_flush_timer()
        
        atexit.register(self.shutdown)

        self.debug("LuminaLog SDK initialized", {"environment": self.environment})

    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message"""
        self._log("debug", message, metadata)

    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message"""
        self._log("info", message, metadata)

    def warn(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message"""
        self._log("warn", message, metadata)

    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message"""
        self._log("error", message, metadata)

    def fatal(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a fatal error message"""
        self._log("fatal", message, metadata)

    def panic(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a panic message and flush immediately"""
        entry = self._create_entry("panic", message, metadata)
        with self._queue_lock:
            self._queue.append(entry)
        self.flush()

    def child(self, metadata: Dict[str, Any]) -> "LuminaLog":
        """
        Create a child logger with additional context metadata
        
        Args:
            metadata: Additional metadata to include in all logs from this child logger
            
        Returns:
            A new LuminaLog instance with merged metadata
        """
        child_logger = LuminaLog(
            api_key=self.api_key,
            environment=self.environment,
            project_id=self.project_id,
            privacy_mode=self.privacy_mode,
            min_level=self.min_level,
            batch_size=self.batch_size,
            flush_interval=self.flush_interval,
            endpoint=self.endpoint,
            debug=self.debug_mode,
        )
        
        child_logger._base_metadata = {**self._base_metadata, **metadata}
        
        return child_logger

    def capture_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Capture an exception with full stack trace
        
        Args:
            error: The exception to capture
            context: Additional context metadata
        """
        error_payload: ErrorPayload = {
            "type": type(error).__name__,
            "message": str(error),
            "stack_trace": traceback.format_tb(error.__traceback__),
            "context": context,
        }

        entry: LogEntry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "error",
            "message": str(error),
            "environment": self.environment,
            "privacy_mode": self.privacy_mode,
            "error": error_payload,
            "metadata": context,
        }

        if self.project_id:
            entry["project_id"] = self.project_id

        with self._queue_lock:
            self._queue.append(entry)

        if len(self._queue) >= self.batch_size:
            self.flush()

    def capture_exception(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Alias for capture_error"""
        self.capture_error(error, context)

    def flush(self) -> None:
        """Flush all queued logs immediately"""
        if self._is_flushing or self._shutdown:
            return

        with self._queue_lock:
            if not self._queue:
                return

            self._is_flushing = True
            logs_to_send = self._queue.copy()
            self._queue.clear()

        try:
            self._send_batch(logs_to_send)
            if self.debug_mode:
                print(f"[LuminaLog] Flushed {len(logs_to_send)} logs")
        except Exception as e:
            with self._queue_lock:
                self._queue = logs_to_send + self._queue
            if self.debug_mode:
                print(f"[LuminaLog] Failed to flush logs: {e}")
        finally:
            self._is_flushing = False

    def shutdown(self) -> None:
        """Shutdown the logger and flush remaining logs"""
        if self._shutdown:
            return

        self._shutdown = True
        self._stop_flush_timer()
        self.flush()

    def _log(
        self, level: LogLevel, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Internal logging method"""
        if self.min_level and not self._should_log(level):
            return
            
        entry = self._create_entry(level, message, metadata)
        
        with self._queue_lock:
            self._queue.append(entry)

        if len(self._queue) >= self.batch_size:
            self.flush()

    def _should_log(self, level: LogLevel) -> bool:
        """Check if a log level should be logged based on min_level setting"""
        if not self.min_level:
            return True
            
        min_index = self._log_levels.index(self.min_level)
        current_index = self._log_levels.index(level)
        
        return current_index >= min_index

    def _create_entry(
        self, level: LogLevel, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> LogEntry:
        """Create a log entry"""
        final_metadata = {**self._base_metadata, **(metadata or {})}
        
        entry: LogEntry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "environment": self.environment,
            "privacy_mode": self.privacy_mode,
            "metadata": final_metadata if final_metadata else None,
        }

        if self.project_id:
            entry["project_id"] = self.project_id

        return entry

    def _start_flush_timer(self) -> None:
        """Start periodic flush timer"""
        if self._shutdown:
            return

        self._flush_timer = threading.Timer(self.flush_interval, self._on_flush_timer)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _stop_flush_timer(self) -> None:
        """Stop periodic flush timer"""
        if self._flush_timer:
            self._flush_timer.cancel()
            self._flush_timer = None

    def _on_flush_timer(self) -> None:
        """Timer callback to flush logs"""
        self.flush()
        self._start_flush_timer()

    def _send_batch(self, logs: List[LogEntry]) -> IngestionResponse:
        """Send a batch of logs to the API with retry logic"""
        batch: LogBatch = {
            "api_key": self.api_key,
            "logs": logs,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "luminalog-python/0.1.0",
        }

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.endpoint,
                    json=batch,
                    headers=headers,
                    timeout=10,
                )

                if response.status_code == 429:
                    print(
                        "[LuminaLog] 🚨 LOG QUOTA EXCEEDED: Your plan limit has been reached. "
                        "Logs will be dropped until you upgrade. "
                        "Visit your dashboard to upgrade: https://luminalog.cloud/dashboard/billing"
                    )
                    return {"message": "Quota Exceeded - Logs Dropped", "processed": 0}

                response.raise_for_status()
                
                try:
                    result = response.json()
                    if "debug_user_id" not in result and self.debug_mode:
                        print("Warning: No debug_user_id in response")
                    return result
                except json.JSONDecodeError:
                    return {"message": "OK", "processed": len(logs)}

            except requests.RequestException as e:
                is_last_attempt = attempt == max_retries - 1
                
                if is_last_attempt:
                    raise Exception(f"Failed to send logs after {max_retries} attempts: {e}")
                
                delay = base_delay * (2 ** attempt)
                if self.debug_mode:
                    print(f"[LuminaLog] Attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
