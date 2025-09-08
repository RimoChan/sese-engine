"""
Configuration settings for sese-engine.

This module contains all configuration parameters for the search engine,
including crawler settings, indexing parameters, and search behavior.
"""

from pathlib import Path
from typing import List, Dict, Any
import os


class Config:
    """Configuration class for sese-engine."""
    
    # Storage settings
    STORAGE_PATH: Path = Path(os.getenv('SESE_STORAGE_PATH', './savedata'))
    
    # Index settings
    MAX_URLS_PER_KEYWORD: int = 11000  # Max URLs per keyword index
    MAX_URLS_PER_KEYWORD_SAME_DOMAIN: int = 20  # Max URLs from same domain per keyword
    MAX_CLEANUP_ROWS: int = 10000000  # Rows to process in cleanup
    MAX_NEW_URLS_PER_KEYWORD: int = 10000  # Max new URLs to add per keyword
    MIN_URLS_FOR_NEW_KEYWORD: int = 3  # Min URLs needed to create new keyword
    
    # Crawler settings
    CRAWLER_NAME: str = 'sese_spider'
    CRAWLER_COOLDOWN: int = 3  # Seconds between requests
    CRAWLER_THREADS: int = 22  # Number of crawler threads
    CRAWLER_CONCENTRATION: float = 0.7  # Concentration on single domains (0-1)
    MAX_KEYWORDS_PER_PAGE: int = 250  # Max keywords to extract per page
    MAX_EPOCH: int = 100  # Maximum epochs for crawling
    PROSPEROUS_SITE_RATIO: float = 0.6  # Ratio of prosperous sites per epoch
    START_URL: str = 'https://zh.wikipedia.org/'
    
    # Search settings
    USE_ONLINE_SUMMARY: bool = True  # Fetch online summaries for results
    ONLINE_SUMMARY_TIMEOUT: int = 3  # Timeout for online summary requests
    WEIGHT_DAILY_DECAY: float = 0.996  # Daily weight decay factor
    LANGUAGE_WEIGHT: float = 0.5  # Weight for Chinese content
    CONSECUTIVE_KEYWORD_WEIGHT: float = 1.3  # Weight for consecutive keywords
    BACKLINK_WEIGHT: float = 1.0  # Weight for backlinks
    DEMOTION_KEYWORDS: List[str] = []  # Keywords that demote results
    DEMOTION_KEYWORD_WEIGHT: float = 0.1  # Weight for demotion keywords
    
    # Server settings
    SERVER_PORT: int = int(os.getenv('SESE_PORT', 8080))
    SERVER_HOST: str = os.getenv('SESE_HOST', '0.0.0.0')
    
    # Backlink settings
    BACKLINK_BASE_VALUE: int = 200000  # Base value for backlink calculations
    
    # Performance settings
    MAX_QUEUE_SIZE: int = 300000  # Maximum queue size for processing
    
    @classmethod
    def get_crawler_config(cls) -> Dict[str, Any]:
        """Get crawler-specific configuration."""
        return {
            'name': cls.CRAWLER_NAME,
            'cooldown': cls.CRAWLER_COOLDOWN,
            'threads': cls.CRAWLER_THREADS,
            'concentration': cls.CRAWLER_CONCENTRATION,
            'max_keywords_per_page': cls.MAX_KEYWORDS_PER_PAGE,
            'max_epoch': cls.MAX_EPOCH,
            'prosperous_ratio': cls.PROSPEROUS_SITE_RATIO,
            'start_url': cls.START_URL,
        }
    
    @classmethod
    def get_search_config(cls) -> Dict[str, Any]:
        """Get search-specific configuration."""
        return {
            'use_online_summary': cls.USE_ONLINE_SUMMARY,
            'online_summary_timeout': cls.ONLINE_SUMMARY_TIMEOUT,
            'weight_daily_decay': cls.WEIGHT_DAILY_DECAY,
            'language_weight': cls.LANGUAGE_WEIGHT,
            'consecutive_keyword_weight': cls.CONSECUTIVE_KEYWORD_WEIGHT,
            'backlink_weight': cls.BACKLINK_WEIGHT,
            'demotion_keywords': cls.DEMOTION_KEYWORDS,
            'demotion_keyword_weight': cls.DEMOTION_KEYWORD_WEIGHT,
        }
    
    @classmethod
    def get_index_config(cls) -> Dict[str, Any]:
        """Get index-specific configuration."""
        return {
            'max_urls_per_keyword': cls.MAX_URLS_PER_KEYWORD,
            'max_urls_per_keyword_same_domain': cls.MAX_URLS_PER_KEYWORD_SAME_DOMAIN,
            'max_cleanup_rows': cls.MAX_CLEANUP_ROWS,
            'max_new_urls_per_keyword': cls.MAX_NEW_URLS_PER_KEYWORD,
            'min_urls_for_new_keyword': cls.MIN_URLS_FOR_NEW_KEYWORD,
        }


# Global configuration instance
config = Config()