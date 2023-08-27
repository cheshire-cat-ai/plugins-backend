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
    cache_path = "zip_cache/versions.json"

    # Load existing versions from the JSON file
    if os.path.exists(cache_path):
        with open(cache_path, "r") as json_file:
            versions = json.load(json_file)
    else:
        versions = []
        
    # Search for the plugin by name_plugin
    plugin_found = False
    for index, matching_plugins in enumerate(versions):
        if matching_plugins["name_plugin"] == name_plugin:
            plugin_found = not plugin_found
            data = versions[index]
            data["version"] = version
    # If plugin not found, add it
    if not plugin_found:
        versions.append({"name_plugin": name_plugin, "version": version})
    
    # Save the updated list of versions to a variable
    updated_versions = versions
    
    # Write the updated list back to the JSON file
    with open(cache_path, "w") as json_file:
        json.dump(updated_versions, json_file, indent=4)
        
        
        

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
