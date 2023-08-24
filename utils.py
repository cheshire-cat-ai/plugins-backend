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


def update_version_zip(name_plugin: str, version: str):
    with open("zip_cache/versions.json", "r+") as json_file:
        versions: list[dict] = json.load(json_file)
        if len(versions) != 0:
            for index, matching_plugins in enumerate(versions):
                #update
                if matching_plugins.get("name_plugin") == name_plugin:
                    data = versions[index]
                    data["version"] = version
        else:
            plugin_version = {
                    "name_plugin": name_plugin,
                    "version": version
            }
            versions.append(plugin_version)
        
        json_file.seek(0)  # Move to the beginning of the file
        json_file.truncate()  # Clear the existing content
        json.dump(versions,json_file)
        

def check_version_zip(name_plugin: str, version: str) -> bool:
    """
    Check if the cached plugin is updated.
    
    Returns:
        False if is not updated or not exist otherwise return True
    """
    # Define a cache directory
    cache_json = "zip_cache/" + "versions.json"
    if not os.path.exists(cache_json):
            with open(cache_json, "w") as json_file:
                data = []
                json.dump(data,json_file)
                return False
    else:
        with open(cache_json, "r") as json_file:
            versions: list[dict] = json.load(json_file) 
            matching_plugins = [plugin for plugin in versions if plugin.get("name_plugin") == name_plugin]
            if matching_plugins:
                cache_version = matching_plugins[0]["version"]
                if cache_version == version:
                    return True
            
            return False
