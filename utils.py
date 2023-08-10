from datetime import datetime, timedelta
import os
from fastapi import HTTPException
import httpx
import json

def is_cache_valid(cache_duration: int, cache_timestamp: dict):
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


def check_version_zip(name_plugin: str, version: int) -> bool:
    """
    Check if the cached plugin is updated.
    
    Returns:
        False if is not updated or not exist (will be updated) otherwise return True
    """
    # Define a cache directory
    cache_json = "zip_cache/" + "versions.json"
    if not os.path.exists(cache_json):
        with open(cache_json, "w") as json_file:
                data = []
                json.dump(data,json_file)
                json_file.close() #idk why but if you don't have it, the code crash...
                
    with open(cache_json, "r") as json_file:
    
            versions: list[dict] = json.load(json_file) 
            
            matching_plugins = [plugin for plugin in versions if plugin.get("name_plugin") == name_plugin]
            json_file.close()
            
    with open(cache_json, "w") as json_file: 
        if matching_plugins:
            matching_plugins = matching_plugins[0]
            cache_version = matching_plugins["version"]
            if cache_version != version:
                versions.remove(matching_plugins)
                matching_plugins["version"] = version
                versions.append(matching_plugins)
                json.dump(versions,json_file)
                return False
            else:
                return True
        else:
            data = {
                "name_plugin": name_plugin,
                "version": version
            }
            versions.append(data)
            json.dump(versions,json_file)
            return False
                
            
    
    
    