#!/usr/bin/env python3
"""
Run the Scholarship Copilot FastAPI server
"""

import uvicorn
import logging
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run the server"""
    logger.info(f"Starting Scholarship Copilot in {settings.environment} mode")
    logger.info(f"Server: {settings.fastapi_host}:{settings.fastapi_port}")
    logger.info(f"Claude Model: {settings.claude_model}")

    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
