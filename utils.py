from datetime import datetime, timedelta
import httpx


def is_cache_valid(cache_duration, cache_timestamp):
    """
    Check if the cache is still valid based on the cache duration.
    """
    if "plugins" not in cache_timestamp:
        return False
    cache_time = cache_timestamp["plugins"]
    return datetime.utcnow() < cache_time + timedelta(minutes=cache_duration)


async def fetch_plugin_json(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

