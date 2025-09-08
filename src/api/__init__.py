"""
FastAPI search server for sese-engine.

This module provides a modern, async web API for the search engine
with improved error handling, validation, and performance.
"""

import re
import time
import json
import math
import heapq
import logging
import asyncio
from typing import List, Tuple, Optional, Dict, Any
from urllib.parse import unquote
from contextlib import asynccontextmanager

import jieba
import httpx
import Levenshtein
import prometheus_client
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ..config import config
from ..storage import StorageManager, IndexSpace, FusionGate
from ..utils import (
    extract_netloc, tokenize_text, calculate_url_penalty, 
    decompose_url, detect_language, log_exception
)
from ..types import SearchResult, ScoredURL


class SearchError(Exception):
    """Base exception for search-related errors."""
    pass


class QueryValidationError(SearchError):
    """Exception raised when query validation fails."""
    pass


class SearchService:
    """Core search service implementation."""
    
    def __init__(self, storage_manager: StorageManager):
        """Initialize search service."""
        self.storage = storage_manager
        self.keyword_index: IndexSpace = storage_manager.keyword_index
        self.metadata_gate: FusionGate = storage_manager.url_metadata
        self.site_info: FusionGate = storage_manager.site_info
        
        # Load configuration
        self.search_config = config.get_search_config()
        self.index_config = config.get_index_config()
        
        # Initialize cached data
        self._blocked_keywords = self._load_blocked_keywords()
        self._domain_adjustments = self._load_domain_adjustments()
        self._prosperity_data = self._load_prosperity_data()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_blocked_keywords(self) -> set:
        """Load blocked keywords from data file."""
        try:
            with open('./data/blocked_keywords.json', 'r', encoding='utf8') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()
    
    def _load_domain_adjustments(self) -> dict:
        """Load domain adjustment factors."""
        try:
            import yaml
            with open('./data/domain_adjustments.yaml', 'r', encoding='utf8') as f:
                return yaml.safe_load(f) or {}
        except (FileNotFoundError, yaml.YAMLError):
            return {}
    
    def _load_prosperity_data(self) -> dict:
        """Load prosperity data for domains."""
        try:
            with open(config.STORAGE_PATH / 'prosperity.json', 'r', encoding='utf8') as f:
                data = json.load(f)
                return self._normalize_prosperity(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _normalize_prosperity(self, data: dict) -> dict:
        """Normalize prosperity data."""
        base_values = [v for k, v in data.items() if '/' not in k]
        total_energy = sum(base_values)
        if total_energy == 0:
            return data
        
        scale_factor = config.BACKLINK_BASE_VALUE / total_energy
        normalized = {k: v * scale_factor for k, v in data.items()}
        
        # Propagate values to subdomains
        for domain in list(normalized.keys()):
            if '.' in domain:
                parts = domain.split('.')
                for i in range(1, len(parts)):
                    parent = '.'.join(parts[i:])
                    if parent in normalized and normalized[parent] < normalized[domain]:
                        normalized[parent] = normalized[domain]
        
        return normalized
    
    def _parse_query(self, query: str) -> Tuple[List[str], Optional[str]]:
        """Parse search query and extract keywords and site filter."""
        keywords = []
        site_filter = None
        
        for term in query.split():
            if term.startswith('site:'):
                site_filter = term[5:]
            else:
                # Tokenize the term
                tokens = tokenize_text(term, search_mode=False)
                keywords.extend(tokens)
        
        # Filter out blocked keywords
        filtered_keywords = [k for k in keywords if k not in self._blocked_keywords]
        
        if len(filtered_keywords) > 20:
            raise QueryValidationError("Too many keywords in query")
        
        return filtered_keywords, site_filter
    
    def _calculate_consecutive_bonus(self, text: str, keywords: List[str]) -> int:
        """Calculate bonus for consecutive keywords."""
        return sum(1 for a, b in zip(keywords[:-1], keywords[1:]) if a + b in text)
    
    def _calculate_similarity_penalty(self, titles: List[str]) -> List[float]:
        """Calculate penalty for similar titles."""
        def similarity(a: str, b: str) -> float:
            if not a or not b:
                return 0
            return 1 - Levenshtein.distance(a, b) / max(len(a), len(b))
        
        penalties = []
        if titles:
            seen = {titles[0]}
            penalties.append(0)
            
            for title in titles[1:]:
                max_sim = max((similarity(title, s) for s in seen), default=0)
                penalties.append(max_sim)
                seen.add(title)
        
        return penalties
    
    async def _get_site_info(self, domain: str) -> dict:
        """Get site information with caching."""
        cache_key = f"site_info:{domain}:{int(time.time()) // (3600 * 24)}"
        
        # This would use a proper cache in production
        try:
            site_data = self.site_info.get(domain, {})
            return {
                'access_count': site_data.get('access_count', 0),
                'last_access_time': site_data.get('last_access_time', 0),
                'language': site_data.get('language', {}),
                'keywords': site_data.get('keywords', []),
                'success_rate': site_data.get('success_rate', 1.0),
            }
        except KeyError:
            return {
                'access_count': 0,
                'last_access_time': 0,
                'language': {},
                'keywords': [],
                'success_rate': 1.0,
            }
    
    async def _get_page_metadata(self, url: str) -> Optional[Tuple[str, str, str]]:
        """Get page metadata (title, description, text)."""
        if not self.search_config['use_online_summary']:
            return None
        
        try:
            # This would be implemented to fetch and parse the page
            # For now, return cached data if available
            cached_data = self.metadata_gate.get(url, None)
            if cached_data and len(cached_data) >= 3:
                return cached_data[:3]
            
            # Async implementation would go here
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get metadata for {url}: {e}")
            return None
    
    def _generate_preview(self, keywords: List[str], text: str) -> str:
        """Generate search result preview."""
        window_size = 32
        last_positions = {kw: -1 for kw in keywords}
        
        tokens = jieba.lcut(text[:1000])
        best_match = (0, 0)
        
        for i, token in enumerate(tokens):
            token_lower = token.lower()
            if token_lower in last_positions:
                last_positions[token_lower] = i
                matches = sum(1 for pos in last_positions.values() if pos > i - window_size)
                if matches > best_match[0]:
                    best_match = (matches, i)
        
        if best_match[0] == 0:
            return ''
        
        center = best_match[1]
        if center < window_size:
            start, end = 0, window_size + 12
        else:
            start, end = center - window_size, center + 12
        
        preview = ''.join(tokens[start:end])
        if len(tokens) > end:
            preview += '...'
        
        return preview
    
    async def search(self, query: str, offset: int = 0, limit: int = 10, 
                   site_filter: Optional[str] = None) -> Tuple[List[SearchResult], int]:
        """
        Execute search query.
        
        Args:
            query: Search query string
            offset: Result offset for pagination
            limit: Maximum number of results
            site_filter: Optional site restriction
            
        Returns:
            Tuple of (results, total_count)
        """
        start_time = time.time()
        
        try:
            # Parse query
            keywords, extracted_site = self._parse_query(query)
            if extracted_site:
                site_filter = extracted_site
            
            if not keywords:
                return [], 0
            
            # Get initial results
            results, total_count = await self._execute_search(keywords, offset, limit, site_filter)
            
            self.logger.info(f"Search completed in {time.time() - start_time:.3f}s: "
                           f"query='{query}', results={len(results)}, total={total_count}")
            
            return results, total_count
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            raise SearchError(f"Search execution failed: {e}")
    
    async def _execute_search(self, keywords: List[str], offset: int, limit: int, 
                             site_filter: Optional[str]) -> Tuple[List[SearchResult], int]:
        """Execute the actual search logic."""
        # This is a simplified version - the full implementation would include
        # all the complex ranking logic from the original code
        
        # Get URLs for each keyword
        url_scores = {}
        default_scores = {}
        
        for keyword in keywords:
            try:
                keyword_urls = self.keyword_index.get(keyword, [])
                default_scores[keyword] = self._calculate_default_score(keyword_urls)
                
                for score, url in keyword_urls:
                    url_scores.setdefault(url, {})[keyword] = score
            except KeyError:
                default_scores[keyword] = 1e-4
        
        # Filter and rank results
        candidates = list(url_scores.items())
        if site_filter:
            candidates = [(url, scores) for url, scores in candidates 
                         if site_filter in url]
        
        total_count = len(candidates)
        
        # Calculate relevance scores
        ranked_results = []
        for url, keyword_scores in candidates:
            relevance = self._calculate_relevance(keyword_scores, default_scores, keywords)
            ranked_results.append((relevance, url))
        
        # Sort by relevance
        ranked_results.sort(reverse=True)
        
        # Generate search results
        results = []
        for i, (score, url) in enumerate(ranked_results[offset:offset + limit]):
            result = await self._build_search_result(url, score, keyword_scores.get(url, {}), keywords)
            results.append(result)
        
        return results, total_count
    
    def _calculate_default_score(self, keyword_urls: ScoredURL) -> float:
        """Calculate default score for keyword."""
        if len(keyword_urls) < self.index_config['max_urls_per_keyword']:
            return 1e-4 * (max(100, len(keyword_urls)) / self.index_config['max_urls_per_keyword'])
        else:
            sorted_scores = sorted([score for score, _ in keyword_urls], reverse=True)
            threshold_score = sorted_scores[self.index_config['max_urls_per_keyword']]
            return max(1e-4, threshold_score / 2)
    
    def _calculate_relevance(self, keyword_scores: Dict[str, float], 
                           default_scores: Dict[str, float], keywords: List[str]) -> float:
        """Calculate relevance score for a URL."""
        relevance = 1.0
        
        for keyword in keywords:
            score = keyword_scores.get(keyword, default_scores[keyword])
            if score > 0.06:
                score = math.log((score - 0.06) * 40 + 1) / 40 + 0.06
            relevance *= score
        
        return relevance
    
    async def _build_search_result(self, url: str, relevance_score: float, 
                                  keyword_scores: Dict[str, float], keywords: List[str]) -> SearchResult:
        """Build a search result object."""
        # Get metadata
        metadata = await self._get_page_metadata(url)
        
        # Get domain info
        domain = extract_netloc(url)
        site_info = await self._get_site_info(domain)
        
        # Calculate various scoring factors
        url_penalty = calculate_url_penalty(url)
        domain_adjustment = self._domain_adjustments.get(domain, 1.0)
        prosperity_score = self._prosperity_data.get(domain, 1.0)
        
        # Build result
        result = {
            'score': relevance_score * prosperity_score * (1 - url_penalty) * domain_adjustment,
            'url': unquote(url),
            'domain': domain,
            'relevance_scores': keyword_scores,
            'factors': {
                'relevance': relevance_score,
                'prosperity': prosperity_score,
                'url_penalty': url_penalty,
                'domain_adjustment': domain_adjustment,
            }
        }
        
        if metadata:
            title, description, text = metadata
            result.update({
                'title': title,
                'description': self._generate_preview(keywords, description),
                'snippet': self._generate_preview(keywords, text),
            })
        
        return result


# Global service instance
search_service: Optional[SearchService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global search_service
    
    # Initialize services
    storage_manager = StorageManager(config.STORAGE_PATH)
    search_service = SearchService(storage_manager)
    
    # Start Prometheus metrics
    prometheus_client.start_http_server(14953)
    
    yield
    
    # Cleanup
    search_service = None


# Create FastAPI app
app = FastAPI(
    title="sese-engine API",
    description="Modern search engine API",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/search", response_model=dict)
async def search_endpoint(
    q: str = Query(..., description="Search query"),
    offset: int = Query(0, ge=0, description="Result offset"),
    limit: int = Query(10, ge=1, le=20, description="Number of results"),
    site: Optional[str] = Query(None, description="Site filter (e.g., example.com)"),
):
    """
    Execute search query.
    
    Args:
        q: Search query string
        offset: Result offset for pagination
        limit: Maximum number of results to return
        site: Optional site restriction
        
    Returns:
        Search results with metadata
    """
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not available")
    
    try:
        results, total_count = await search_service.search(q, offset, limit, site)
        
        return {
            "query": q,
            "keywords": search_service._parse_query(q)[0],
            "results": results,
            "total": total_count,
            "offset": offset,
            "limit": limit,
        }
        
    except QueryValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SearchError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sese-engine"}


@app.get("/metrics")
async def get_metrics():
    """Get basic metrics."""
    if not search_service:
        return {"status": "initializing"}
    
    return {
        "indexed_keywords": len(search_service.keyword_index),
        "storage_stats": search_service.storage.get_storage_stats(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=True
    )