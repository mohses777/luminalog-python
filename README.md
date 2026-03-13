<div align="center">
  <h1>luminalog-sdk</h1>
  <p>Privacy-first logging with AI-powered debugging for Python</p>
  
  [![PyPI version](https://img.shields.io/pypi/v/luminalog-sdk.svg)](https://pypi.org/project/luminalog-sdk/)
  [![Python Versions](https://img.shields.io/pypi/pyversions/luminalog-sdk.svg)](https://pypi.org/project/luminalog-sdk/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  
  <p>
    <a href="#installation">Installation</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#documentation">Documentation</a> •
    <a href="#examples">Examples</a> •
    <a href="#support">Support</a>
  </p>
</div>

---

## Features

- 🔒 **Privacy-First** - Automatic PII scrubbing on the server
- ⚡ **Zero Performance Impact** - Async batching (100 logs or 5s intervals)
- 🛡️ **Graceful Degradation** - Queues logs locally if API is unavailable
- 📦 **Type Hints** - Full type annotations for Python 3.8+
- 🪶 **Minimal Dependencies** - Only requires `requests`
- 🎯 **Error Tracking** - Automatic error grouping and stack traces
- 🔄 **Thread-Safe** - Safe for multi-threaded applications
- 📊 **Quota Management** - Built-in quota exceeded handling

## Installation

```bash
pip install luminalog-sdk
```

```bash
poetry add luminalog-sdk
```

```bash
pipenv install luminalog-sdk
```

## Quick Start

```python
from luminalog import LuminaLog
import os

logger = LuminaLog(
    api_key=os.getenv("LUMINALOG_API_KEY"),
    environment="production"
)

# Basic logging
logger.info("User logged in", {"user_id": "123"})
logger.warn("High memory usage", {"memory_mb": 512})
logger.error("Payment failed", {"error": "Card declined"})

# Critical errors (sent immediately, bypasses batching)
logger.panic("Database connection lost!")

# Graceful shutdown
logger.shutdown()
```

## Configuration

### Options

```python
logger = LuminaLog(
    # Required
    api_key: str,              # Your LuminaLog API key

    # Optional
    environment: str = "default",     # Environment name (default: 'default')
    project_id: str = None,           # Project identifier
    batch_size: int = 100,            # Logs before auto-flush (default: 100)
    flush_interval: float = 5.0,      # Seconds between flushes (default: 5.0)
    endpoint: str = None,             # Custom API endpoint
    debug: bool = False,              # Enable debug logging (default: False)
)
```

### Environment Variables

Store your API key securely using environment variables:

```bash
# .env
LUMINALOG_API_KEY=your-api-key-here
```

```python
import os
from luminalog import LuminaLog

logger = LuminaLog(
    api_key=os.getenv("LUMINALOG_API_KEY"),
    environment=os.getenv("ENVIRONMENT", "development")
)
```

## API Reference

### Log Levels

| Level   | Method           | Description                    | Behavior        |
| ------- | ---------------- | ------------------------------ | --------------- |
| `debug` | `logger.debug()` | Detailed debugging information | Batched         |
| `info`  | `logger.info()`  | General operational messages   | Batched         |
| `warn`  | `logger.warn()`  | Warning conditions             | Batched         |
| `error` | `logger.error()` | Error conditions               | Batched         |
| `fatal` | `logger.fatal()` | Fatal errors                   | Batched         |
| `panic` | `logger.panic()` | Critical errors                | Immediate flush |

### Methods

#### `logger.debug(message, metadata=None)`
Log a debug message.

#### `logger.info(message, metadata=None)`
Log an informational message.

#### `logger.warn(message, metadata=None)`
Log a warning message.

#### `logger.error(message, metadata=None)`
Log an error message.

#### `logger.fatal(message, metadata=None)`
Log a fatal error.

#### `logger.panic(message, metadata=None)`
Log a critical error and flush immediately.

#### `logger.capture_error(error, context=None)`
Capture an exception with full stack trace.

```python
try:
    risky_operation()
except Exception as e:
    logger.capture_error(e, {
        "user_id": "123",
        "operation": "payment_processing"
    })
```

### Distributed Tracing Correlation

Manage trace and span identifiers for distributed system grouping.

#### `generate_trace_id()`
Generates a unique Trace ID (UUID v4) string.

#### `generate_span_id()`
Generates a unique Span ID string.

#### `get_trace_id_from_request(request)`
Extracts Trace ID from standard headers (`x-trace-id`, `x-request-id`, or W3C `traceparent`). Works with Flask, FastAPI, and Django requests.

```python
from luminalog import generate_trace_id, get_trace_id_from_request

trace_id = get_trace_id_from_request(flask_request)
```

## Examples

### Flask

```python
from flask import Flask, request
from luminalog import LuminaLog
import os

app = Flask(__name__)
logger = LuminaLog(api_key=os.getenv("LUMINALOG_API_KEY"))

@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path}", {
        "ip": request.remote_addr,
        "user_agent": request.user_agent.string
    })

@app.errorhandler(Exception)
def handle_error(error):
    logger.capture_error(error, {
        "path": request.path,
        "method": request.method
    })
    return "Internal Server Error", 500

if __name__ == "__main__":
    try:
        app.run()
    finally:
        logger.shutdown()
```

### FastAPI

```python
from fastapi import FastAPI, Request
from luminalog import LuminaLog
import os

app = FastAPI()
logger = LuminaLog(api_key=os.getenv("LUMINALOG_API_KEY"))

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}", {
        "client": request.client.host,
        "user_agent": request.headers.get("user-agent")
    })
    response = await call_next(request)
    return response

@app.on_event("shutdown")
async def shutdown_event():
    logger.shutdown()
```

### AWS Lambda

```python
from luminalog import LuminaLog
import os

logger = LuminaLog(api_key=os.getenv("LUMINALOG_API_KEY"))

def lambda_handler(event, context):
    try:
        logger.info("Lambda invoked", {"event_type": event.get("type")})
        # Logic...
    except Exception as e:
        logger.capture_error(e, {"event": event})
        raise
    finally:
        logger.shutdown()
```

## Documentation

- 📘 [Full Documentation](https://luminalog.cloud/docs)
- 🚀 [Quick Start Guide](https://luminalog.cloud/docs/quick-start)
- 📖 [Python SDK Reference](https://luminalog.cloud/docs/sdk/python)
- � [REST API Reference](https://luminalog.cloud/docs/sdk/rest-api)

## Support

- 🐛 [Report a Bug](https://github.com/mohses777/luminalog-python/issues)
- 📧 [Email Support](mailto:support@luminalog.cloud)
- 𝕏 [Twitter / X](https://x.com/LuminaLogCloud)

## Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## License

MIT © [LuminaLog Team](https://luminalog.cloud)

---

<div align="center">
  <p>Built with ❤️ by the LuminaLog team</p>
  <p>
    <a href="https://luminalog.cloud">Website</a> •
    <a href="https://luminalog.cloud/docs">Docs</a> •
    <a href="https://x.com/LuminaLogCloud">Twitter</a> •
    <a href="https://github.com/mohses777/luminalog-python">GitHub</a>
  </p>
</div>
