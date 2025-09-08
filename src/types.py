"""
Type definitions for sese-engine.

This module provides common type aliases used throughout the codebase.
"""

from typing import List, Tuple, Dict, Optional, Any, Union, Iterator

# Basic types
ScoredURL = List[Tuple[float, str]]
URLList = List[str]
Keyword = str
URL = str
Score = float

# Data structures
KeywordIndex = Dict[Keyword, ScoredURL]
DomainStats = Dict[str, Any]
SearchResult = Dict[str, Any]
CrawlerTask = Dict[str, Any]
IndexTask = Dict[str, Any]

# Configuration types
ConfigDict = Dict[str, Any]
SearchConfig = Dict[str, Any]
CrawlerConfig = Dict[str, Any]
IndexConfig = Dict[str, Any]

# Optional types
OptionalURL = Optional[URL]
OptionalScore = Optional[Score]
OptionalKeyword = Optional[Keyword]

# Iterator types
URLIterator = Iterator[URL]
ScoredURLIterator = Iterator[Tuple[Score, URL]]
TaskIterator = Iterator[CrawlerTask]

# JSON types
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONObject = Dict[str, JSONValue]
JSONArray = List[JSONValue]