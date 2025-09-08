"""
Utility functions for sese-engine.

This module provides various utility functions for URL processing, 
text processing, error handling, and performance optimization.
"""

import re
import os
import json
import logging
import traceback
import threading
from functools import lru_cache
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Tuple, List, Optional, Any, Dict
from prometheus_client import Counter

import lxml.html
import jieba
from tqdm import tqdm


# Type aliases
ScoredURL = List[Tuple[float, str]]


class EfficientThreadPoolExecutor(ThreadPoolExecutor):
    """
    Memory-efficient ThreadPoolExecutor that avoids excessive memory usage
    in the map method by processing results incrementally.
    """
    
    _nothing = object()
    
    def map(self, fn, *iterables):
        """Map function with memory-efficient processing."""
        lock = threading.Lock()
        z = [*zip(*iterables)][::-1]
        res = [EfficientThreadPoolExecutor._nothing] * len(z)
        
        def get_next_task():
            """Get the next task to execute."""
            with lock:
                if z:
                    task_data = z.pop()
                    future = self.submit(execute_task, fn, *task_data)
                    res[len(z)] = future
        
        def execute_task(fn, *args, **kwargs):
            """Execute task and schedule next one."""
            result = fn(*args, **kwargs)
            get_next_task()
            return result
        
        # Start initial tasks
        for _ in range(min(len(z), self._max_workers)):
            get_next_task()
        
        def result_iterator():
            """Yield results as they complete."""
            nonlocal z
            try:
                while res:
                    future = res.pop()
                    if future is not EfficientThreadPoolExecutor._nothing:
                        yield future.result()
            finally:
                with lock:
                    z = []
                    for future in res:
                        if future is not EfficientThreadPoolExecutor._nothing:
                            future.cancel()
        
        return result_iterator()


@lru_cache(maxsize=100000)
def cached_float(x: str) -> float:
    """Cached float conversion for performance."""
    return float(x)


def json_loads_cached(s: str) -> Any:
    """Load JSON with cached float parsing for memory efficiency."""
    return json.loads(s, parse_float=cached_float)


def extract_netloc(url: str) -> str:
    """
    Extract network location from URL efficiently.
    
    Args:
        url: The URL to parse
        
    Returns:
        The network location (hostname) part of the URL
    """
    try:
        parts = url.split('/')
        netloc_part = parts[2]
        # Basic validation
        assert ('?' not in netloc_part and 
                '\t' not in netloc_part and 
                ' ' not in netloc_part and 
                '\n' not in netloc_part and 
                '\r' not in netloc_part and 
                parts[0] in ('http:', 'https:') and 
                parts[1] == '')
        return netloc_part
    except Exception:
        return urlparse(url).netloc


def gentle_clean(urls: ScoredURL, max_per_domain: int) -> Iterable[Tuple[float, str]]:
    """
    Clean URL list by limiting URLs per domain while preserving root URLs.
    
    Args:
        urls: List of (score, url) tuples
        max_per_domain: Maximum URLs per domain
        
    Yields:
        (score, url) tuples after cleaning
    """
    def is_root_url(url: str) -> bool:
        """Check if URL is a root domain URL."""
        if url.startswith('https://'):
            url = url[8:]
        return len(url.rstrip('/').split('/')) == 1
    
    domain_counts = {}
    for score, url in urls:
        domain = extract_netloc(url).lower()
        if (domain_counts.setdefault(domain, 0) >= max_per_domain and 
            not is_root_url(url)):
            continue
        domain_counts[domain] += 1
        yield score, url


def clean_urls(urls: ScoredURL, max_per_domain: int) -> ScoredURL:
    """Clean URLs and return as list."""
    return list(gentle_clean(urls, max_per_domain))


# Initialize jieba with appropriate logging level
jieba.setLogLevel(logging.INFO)


def tokenize_text(text: str, search_mode: bool = False) -> List[str]:
    """
    Tokenize Chinese text using jieba.
    
    Args:
        text: Text to tokenize
        search_mode: Whether to use search mode tokenization
        
    Returns:
        List of tokens
    """
    # Limit text length for performance
    text = text[:10000]
    tokens = []
    
    for word in text.split():
        try:
            # Check if word is alphanumeric ASCII
            assert word.encode('ascii').isalnum()
        except (UnicodeEncodeError, AssertionError):
            # Non-ASCII word, use Chinese tokenization
            if search_mode:
                tokens.extend(jieba.lcut_for_search(word))
            else:
                tokens.extend(jieba.lcut(word))
        else:
            # ASCII word, keep as is
            tokens.append(word)
    
    return tokens


def calculate_url_penalty(url: str) -> float:
    """
    Calculate penalty score for URL based on various factors.
    
    Args:
        url: URL to evaluate
        
    Returns:
        Penalty score between 0 and 0.9
    """
    penalty = max(0, (len(url) - 30) / 200)
    
    if '.htm' in url or '.php' in url:
        penalty += (1 - penalty) * 0.3
    
    if url.rstrip('/').count('/') > 2:
        penalty += (1 - penalty) * 0.1
    
    if len(url) < 5 or url[4] == ':':  # starts with http:
        penalty += (1 - penalty) * 0.3
    
    return min(penalty, 0.9)


# Global variables for error tracking
_error_counts: Dict[str, int] = {}
_error_counter = None
_prometheus_counter = Counter('errors', 'Error counts', ['type'])


def log_exception(exception: Exception, log_path: Optional[str] = None) -> None:
    """
    Log exception with metrics and optional file logging.
    
    Args:
        exception: The exception to log
        log_path: Optional path to write detailed logs
    """
    global _error_counter, _error_counts
    
    if _error_counter is None:
        _error_counter = tqdm(desc='Total errors', ncols=60)
    
    _error_counter.update(1)
    
    # Get exception type name
    exc_type = type(exception)
    type_name = exc_type.__name__
    if exc_type.__module__ != 'builtins':
        type_name = f"{exc_type.__module__}.{type_name}"
    
    # Update Prometheus metrics
    _prometheus_counter.labels(type=type_name).inc()
    
    # Try to get file and line info
    try:
        tb = exception.__traceback__
        if tb:
            frame = tb.tb_frame
            file_path = frame.f_globals.get('__file__', 'unknown')
            line_no = tb.tb_lineno
            location = f"[{file_path}:{line_no}]{type_name}"
        else:
            location = type_name
    except Exception:
        location = type_name
    
    # Update per-type counter
    if location not in _error_counts:
        _error_counts[location] = tqdm(desc=location, ncols=60)
    _error_counts[location].update(1)
    
    # Write to log file if specified
    if log_path:
        pid = os.getpid()
        filename = f"{log_path}/{pid}.log"
        try:
            with open(filename, 'a', encoding='utf8') as f:
                f.write('=' * 20 + '\n')
                f.write(''.join(traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )))
            
            # Rotate log if too large
            if os.path.getsize(filename) > 50 * 1024 * 1024:  # 50MB
                os.remove(filename)
        except Exception as e:
            print(f"Log failed: {e}!")


# Language detection model
_language_model = None


def detect_language(text: str) -> str:
    """
    Detect language of text using fastText.
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code (e.g., 'zh', 'en')
    """
    global _language_model
    
    if _language_model is None:
        import fasttext
        try:
            # Suppress fastText warnings
            fasttext.FastText.eprint = lambda *args, **kwargs: None
        except Exception:
            pass
        _language_model = fasttext.load_model('lid.176.ftz')
    
    # Clean text for prediction
    clean_text = text.replace('\n', ' ')
    prediction = _language_model.predict(clean_text)[0][0]
    
    # Extract language code from prediction
    assert prediction.startswith('__label__')
    return prediction[9:]


def decompose_url(url: str) -> Optional[Iterable[str]]:
    """
    Decompose URL into hierarchical components.
    
    Args:
        url: URL to decompose
        
    Yields:
        URL components from domain to full path
    """
    url = url.lower()
    
    # Remove protocol
    if url.startswith('https://'):
        url = url[8:]
    elif url.startswith('http://'):
        url = url[7:]
    else:
        return None
    
    # Replace special characters with slash
    url = url.replace('?', '/').replace('#', '/')
    
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    
    # Validate URL
    if not url or url[0] in ' /%':
        return None
    
    # Split into components
    parts = url.split('/')
    current = parts[0]
    yield current
    
    # Yield hierarchical components
    for part in parts[1:]:
        current = f"{current}/{part}"
        yield current


# HTML tag compression mapping
_HTML_TAG_COMPRESSION = {
    'div': 0, 'meta': 1, 'script': 2, 'link': 3, 'h2': 4, 'h3': 5,
    'td': 6, 'input': 7, 'source': 8, 'dd': 9, 'label': 10, 'nav': 11,
    'picture': 12, 'section': 13, 'button': 14, 'dt': 15, 'form': 16,
    'dl': 17, 'head': 18, 'body': 19, 'html': 20, 'title': 21, 'tr': 22,
    'code': 23, 'style': 24, 'strong': 25, 'h4': 26, 'i': 27, 'table': 28,
    'em': 29, 'h1': 30, 'noscript': 31, 'header': 32, 'video': 33,
    'footer': 34, 'b': 35, 'iframe': 36, 'tbody': 37, 'template': 38,
    'hr': 39, 'pre': 40, 'small': 41, 'figure': 42, 'center': 43,
    'main': 44, 'th': 45, 'h5': 46, 'h6': 47, 'fieldset': 48,
    'article': 49, 'var': 50, 'option': 51, 'select': 52, 'font': 53,
    'ol': 54, 'legend': 55, 'track': 56, 'aside': 57, 's': 58,
    'blockquote': 59, 'area': 60, 'base': 61, 'map': 62, 'textarea': 63,
    'big': 64
}


def extract_html_structure(raw_html: str) -> str:
    """
    Extract compressed HTML structure特征。
    
    Args:
        raw_html: Raw HTML content
        
    Returns:
        Compressed JSON structure string
    """
    if not raw_html:
        return ''
    
    try:
        root = lxml.html.document_fromstring(raw_html)
        structure = []
        
        def dfs(element: lxml.html.HtmlElement, current_structure: List) -> None:
            """Depth-first traversal of HTML structure."""
            for child in element:
                # Skip common elements that don't contribute to structure
                if (child.tag in ('a', 'p', 'li', 'ul', 'span', 'img', 'br', 'svg') or
                    not isinstance(child.tag, str)):
                    continue
                
                child_structure = []
                tag_code = _HTML_TAG_COMPRESSION.get(child.tag, child.tag)
                current_structure.append((tag_code, child_structure))
                
                dfs(child, child_structure)
                
                # Simplify if no children
                if current_structure[-1][1] == []:
                    current_structure[-1] = tag_code
        
        dfs([root], structure)
        
        # Convert to JSON and limit length
        return json.dumps(structure, separators=(',', ':'))[:512]
    
    except Exception:
        return ''