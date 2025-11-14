import pytest

from lib.search.engines.base import Result
from lib.search.engines.duckduckgo import DuckDuckGoEngine
from lib.search.engines.brave import BraveEngine
from lib.search.engines.bing import BingEngine
from lib.search.searcher import Searcher, EngineConfig
from lib.search.utils import auto_aclose


@pytest.mark.parametrize("target", [
    "python programming"
])
@pytest.mark.asyncio
@auto_aclose
async def test_search(target: str):
    """Test Searcher can search and return Result object with schemas"""
    searcher = Searcher()
    result = await searcher.search(target, DuckDuckGoEngine())
    print(result)
    assert isinstance(result, Result)
    assert len(result.content) > 0
    return searcher


@pytest.mark.parametrize("target", [
    "python programming"
])
@pytest.mark.asyncio
@auto_aclose
async def test_aggregate_search(target: str):
    """Test Searcher can aggregate results from multiple engines"""
    searcher = Searcher()
    result = await searcher.aggregate_search(target, [
        EngineConfig(BingEngine(), 1),
        EngineConfig(DuckDuckGoEngine(), 2),
    ], 20)
    print(result)
    assert isinstance(result, Result)
    assert result.title == target
    return searcher


@pytest.mark.parametrize("target", [
    "python programming"
])
@pytest.mark.asyncio
@auto_aclose
async def test_aggregate_search_with_time_filter(target: str):
    """Test Searcher can aggregate results with time filter"""
    searcher = Searcher()
    result = await searcher.aggregate_search(target, [
        EngineConfig(DuckDuckGoEngine(), 2),
    ], 10, latest=True)
    print(result)
    assert isinstance(result, Result)
    assert result.title == target
    return searcher


@pytest.mark.parametrize("target", [
    "python programming"
])
@pytest.mark.asyncio
@auto_aclose
async def test_searcher_with_different_result_counts(target: str):
    """Test Searcher with different result count parameters"""
    searcher = Searcher()
    
    # Test with small result count
    result1 = await searcher.aggregate_search(target, [
        EngineConfig(BraveEngine(), 1),
        EngineConfig(DuckDuckGoEngine(), 1),
    ], 3)
    print("With 3 results:", result1)
    assert isinstance(result1, Result)
    
    # Test with larger result count
    result2 = await searcher.aggregate_search(target, [
        EngineConfig(BraveEngine(), 1),
    ], 20)
    print("With 20 results:", result2)
    assert isinstance(result2, Result)
    return searcher


@pytest.mark.parametrize("target", [
    "python programming"
])
@pytest.mark.asyncio
@auto_aclose
async def test_searcher_with_different_engine_weights(target: str):
    """Test Searcher with different engine weights"""
    searcher = Searcher()
    
    # Test with weighted engines
    result = await searcher.aggregate_search(target, [
        EngineConfig(BraveEngine(), 3),      # Higher weight
        EngineConfig(DuckDuckGoEngine(), 1), # Lower weight
    ], 10)
    print("With weighted engines:", result)
    assert isinstance(result, Result)
    assert result.title == target
    return searcher


@pytest.mark.parametrize("target", [
    "python programming"
])
@pytest.mark.asyncio
@auto_aclose
async def test_searcher_with_multiple_engines(target: str):
    """Test Searcher with multiple engines combination"""
    searcher = Searcher()
    
    # Test with three engines
    result = await searcher.aggregate_search(target, [
        EngineConfig(BraveEngine(), 1),
        EngineConfig(DuckDuckGoEngine(), 1),
        EngineConfig(BingEngine(), 1),
    ], 15)
    print("With three engines:", result)
    assert isinstance(result, Result)
    return searcher


@pytest.mark.parametrize("target", [
    "python programming"
])
@pytest.mark.asyncio
@auto_aclose
async def test_searcher_basic_functionality(target: str):
    """Test Searcher basic functionality"""
    searcher = Searcher()
    result = await searcher.search(target, DuckDuckGoEngine())
    print("Basic search functionality:", result)
    assert isinstance(result, Result)
    return searcher


@pytest.mark.asyncio
async def test_extract_domain_function():
    """Test _extract_domain function"""
    from lib.search.searcher import _extract_domain
    
    assert _extract_domain("https://www.example.com/path") == "example.com"
    assert _extract_domain("https://example.com/path") == "example.com"
    assert _extract_domain("https://sub.example.com/path") == "example.com"
    assert _extract_domain("https://user:pass@sub.example.com:8080/path?query=string#fragment") == "example.com"
