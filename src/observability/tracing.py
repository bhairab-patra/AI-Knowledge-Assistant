"""OpenTelemetry setup - traces every FastAPI request, Bedrock call, and HTTP call."""
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config.settings import settings


def setup_tracing(app) -> None:
    """Wire OpenTelemetry into the FastAPI app + boto3 + HTTP libs."""
    resource = Resource.create(
        {
            "service.name": settings.APP_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    # Auto-instrument the libraries we already use
    FastAPIInstrumentor.instrument_app(app)
    BotocoreInstrumentor().instrument()       # captures every Bedrock call
    RequestsInstrumentor().instrument()       # captures WebBaseLoader fetches
    HTTPXClientInstrumentor().instrument()


def get_tracer():
    return trace.get_tracer("rag-pipeline")