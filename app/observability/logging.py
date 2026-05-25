import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging():
    """
    Set up JSON logging for the application
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Create JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    # Create handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(json_formatter)
    
    # Clear existing handlers and add our JSON handler
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Set specific log levels for various modules
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    
    print("Logging setup complete")