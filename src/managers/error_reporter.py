"""
Error reporter using SigNoz for centralized error tracking.
Replaces the old GitHub IssueReporter with OpenTelemetry-based error reporting.
"""

import traceback
import os
from typing import Optional
from src.utils import get_logger


class ErrorReporter:
    """
    Handles error reporting to SigNoz using OpenTelemetry.
    Replaces the GitHub issue creation with centralized observability.
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self._tracer = None
        self._initialized = False

    def _init_tracer(self) -> bool:
        """
        Initialize OpenTelemetry tracer for SigNoz.
        
        Returns:
            True if initialized successfully
        """
        if self._initialized:
            return self._tracer is not None

        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            
            from src.config.constants import (
                get_signoz_endpoint, 
                get_user_id, 
                get_machine_name,
                DAVEAGENT_VERSION,
                is_telemetry_enabled,
            )
            
            if not is_telemetry_enabled():
                self.logger.debug("Telemetry disabled - error reporting inactive")
                self._initialized = True
                return False
            
            # Get configuration
            signoz_url = get_signoz_endpoint()
            user_id = get_user_id()
            machine_name = get_machine_name()
            
            # OTLP HTTP endpoint
            # Allow environment override for specific port/path requirements
            env_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
            if env_endpoint:
                otlp_endpoint = env_endpoint
            else:
                # Default behavior: Assume generic OTLP receiver
                # If using HTTPS on a specific domain without port, assume reverse proxy (443)
                # If localhost or specific IP, usually requires port 4318
                if "localhost" in signoz_url or "127.0.0.1" in signoz_url:
                    otlp_endpoint = f"{signoz_url}:4318/v1/traces"
                else:
                    # For custom domains (like signoz.daveplanet.com), assume 443/ingress handles /v1/traces
                    otlp_endpoint = f"{signoz_url}/v1/traces"
            
            self.logger.debug(f"SigNoz OTLP Endpoint: {otlp_endpoint}")
            
            # Create resource with service info
            resource = Resource.create({
                "service.name": "DaveAgent",
                "service.version": DAVEAGENT_VERSION,
                "host.name": machine_name,
                "user.id": user_id,
            })
            
            # Create tracer provider
            provider = TracerProvider(resource=resource)
            
            # Create OTLP exporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            
            # Add batch processor
            self._processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(self._processor)
            
            # Set as global tracer provider
            trace.set_tracer_provider(provider)
            
            # Get tracer
            self._tracer = trace.get_tracer("daveagent.error_reporter")
            self._initialized = True
            
            self.logger.debug(f"ErrorReporter initialized with SigNoz at {signoz_url}")
            return True
            
        except ImportError as e:
            self.logger.warning(f"OpenTelemetry not installed: {e}")
            self._initialized = True
            return False
        except Exception as e:
            self.logger.warning(f"Failed to initialize ErrorReporter: {e}")
            self._initialized = True
            return False

    async def report_error(
        self, 
        exception: Exception, 
        context: str, 
        model_client=None,  # Kept for compatibility but not used
        severity: str = "error"
    ) -> bool:
        """
        Report an error to SigNoz.
        
        Args:
            exception: The exception object
            context: Description of where the error occurred
            model_client: (Deprecated) Kept for API compatibility
            severity: Error severity level (error, warning, critical)
            
        Returns:
            bool: True if error was reported successfully
        """
        try:
            # Initialize tracer if needed
            if not self._init_tracer():
                self.logger.debug("Error reporting inactive (telemetry disabled or not configured)")
                return False
            
            if not self._tracer:
                return False
            
            # Capture traceback
            tb = traceback.format_exc()
            if not tb or tb == "NoneType: None\n":
                tb = "".join(traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                ))
            
            # Get user info for correlation
            try:
                from src.config.constants import get_user_id, get_machine_name
                user_id = get_user_id()
                machine_name = get_machine_name()
            except Exception:
                user_id = "unknown"
                machine_name = "unknown"
            
            # Create error span
            from opentelemetry import trace
            from opentelemetry.trace import StatusCode
            
            with self._tracer.start_as_current_span("error_report") as span:
                # Set error attributes
                span.set_attribute("error.type", type(exception).__name__)
                span.set_attribute("error.message", str(exception))
                span.set_attribute("error.context", context)
                span.set_attribute("error.severity", severity)
                span.set_attribute("error.traceback", tb[:4096])  # Limit size
                span.set_attribute("user.id", user_id)
                span.set_attribute("host.name", machine_name)
                
                # Record exception
                span.record_exception(exception)
                
                # Set error status
                span.set_status(StatusCode.ERROR, str(exception))
            
            # Force flush to ensure delivery implies we block until sent
            # This prevents lost errors if the application crashes/exits shortly after
            if hasattr(self, "_processor") and self._processor:
                self._processor.force_flush()

            self.logger.info(f"📊 Error reported to SigNoz: {type(exception).__name__} in {context}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to report error to SigNoz: {e}")
            return False

    def report_error_sync(
        self, 
        exception: Exception, 
        context: str,
        severity: str = "error"
    ) -> bool:
        """
        Synchronous version of report_error for use outside async context.
        
        Args:
            exception: The exception object
            context: Description of where the error occurred
            severity: Error severity level
            
        Returns:
            bool: True if error was reported successfully
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new loop for sync execution
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.report_error(exception, context, severity=severity)
                    )
                    return future.result(timeout=5)
            else:
                return loop.run_until_complete(
                    self.report_error(exception, context, severity=severity)
                )
        except Exception:
            return False
