"""OpenTelemetry tracing setup."""
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracing(
    service_name: str,
    otlp_endpoint: str,
    environment: str = "development",
) -> TracerProvider:
    """Configure OpenTelemetry tracing with OTLP gRPC export."""
    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": environment,
            "service.version": "0.1.0",
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return provider
