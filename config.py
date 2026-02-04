#!/usr/bin/env python3
"""Configuration for Polpi MX API"""

import os
from typing import List

class Config:
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database settings
    DB_PATH: str = os.getenv("DB_PATH", "data/polpi.db")
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",  # For React development
        "*"  # Allow all for now
    ]
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Static files
    STATIC_DIR: str = "web"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Investment analysis defaults
    DEFAULT_GROSS_YIELD: float = 0.055  # 5.5% gross rental yield
    APPRECIATION_RATE: float = 0.06    # 6% annual appreciation
    
    # Search settings
    SEARCH_MIN_LENGTH: int = 3
    
    @classmethod
    def load_from_env(cls):
        """Load configuration from environment variables"""
        # Override any settings from environment
        pass

# Create global config instance
config = Config()