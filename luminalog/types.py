"""Type definitions for LuminaLog SDK"""

from typing import Literal, TypedDict, Optional, Dict, Any, List

LogLevel = Literal["debug", "info", "warn", "error", "fatal", "panic"]


class ErrorPayload(TypedDict, total=False):
    """Error payload structure"""
    type: str
    message: str
    stack_trace: List[str]
    fingerprint: Optional[str]
    context: Optional[Dict[str, Any]]


class LogEntry(TypedDict, total=False):
    """Log entry structure"""
    timestamp: str
    level: LogLevel
    message: str
    environment: str
    project_id: Optional[str]
    privacy_mode: Optional[bool]
    error: Optional[ErrorPayload]
    metadata: Optional[Dict[str, Any]]
    trace_id: Optional[str]
    span_id: Optional[str]
    parent_span_id: Optional[str]


class LogBatch(TypedDict):
    """Batch of logs to send"""
    api_key: str
    logs: List[LogEntry]


class IngestionResponse(TypedDict):
    """Response from ingestion API"""
    message: str
    processed: int
