import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from luminalog import LuminaLog, generate_trace_id, generate_span_id  # noqa: E402


def main() -> None:
    logger = LuminaLog(
        api_key=os.getenv("LUMINALOG_API_KEY", "demo-api-key"),
        environment=os.getenv("ENVIRONMENT", "development"),
        project_id="python-basic-example",
        debug=True,
    )

    trace_id = generate_trace_id()
    span_id = generate_span_id()

    logger.info(
        "Python example started",
        {
            "runtime": "python",
            "trace_id": trace_id,
            "span_id": span_id,
        },
    )

    child = logger.child(
        {
            "service": "worker",
            "job": "invoice-generation",
        }
    )

    child.warn(
        "Invoice generation is slower than expected",
        {
            "trace_id": trace_id,
            "span_id": span_id,
            "duration_ms": 1280,
        },
    )

    try:
        raise RuntimeError("Template render failed")
    except Exception as error:
        child.capture_exception(
            error,
            {
                "trace_id": trace_id,
                "span_id": span_id,
                "invoice_id": "inv_123",
            },
        )

    logger.shutdown()


if __name__ == "__main__":
    main()
