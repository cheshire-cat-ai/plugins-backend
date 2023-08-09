from fastapi import HTTPException, APIRouter, Body
from fastapi.responses import FileResponse
from httpx import AsyncClient, RequestError
from datetime import datetime
from utils import is_cache_valid, fetch_plugin_json
from typing import List
import os
import shutil
import git
import zipfile


class Endpoints:

    def __init__(self, app, json, cache_duration, page_size):
        self.cache_duration = cache_duration
        self.json = json
        self.page_size = page_size
        self.app = app
        self.cache = {}
        self.cache_timestamp = {}
        # Define FastAPI endpoints
        self.router = APIRouter()
        self.router.add_api_route("/plugins", self.read_remote_json, methods=["GET"])
        self.router.add_api_route("/tags", self.get_all_tags, methods=["GET"])
        self.router.add_api_route("/tag/{tag_name}", self.get_plugins_by_tag, methods=["GET"])
        self.router.add_api_route("/exclude", self.exclude_plugins, methods=["POST"])
        self.router.add_api_route("/author", self.get_plugins_by_author, methods=["POST"])
        self.router.add_api_route("/download", self.download_plugin_zip, methods=["POST"])
        self.router.add_api_route("/search", self.search_plugins, methods=["POST"])
        self.router.add_api_route("/", self.error, methods=["GET"])
        app.include_router(self.router)

    async def read_remote_json(self, page: int = 1, page_size: int = 0):
        if page_size == 0:
            page_size = self.page_size

        # Check if cache is still valid
        if is_cache_valid(self.cache_duration, self.cache_timestamp):
            cached_plugins = self.cache["plugins"]
        else:
            try:
                async with AsyncClient() as client:
                    response = await client.get(self.json)
                    data = response.json()

                    total_plugins = len(data)
                    start_index = (page - 1) * page_size
                    end_index = start_index + page_size

                    if start_index >= total_plugins:
                        return []

                    cached_plugins = []
                    for entry in data[start_index:end_index]:
                        url = entry["url"]
                        plugin_json_url = url.replace("github.com", "raw.githubusercontent.com") + "/main/plugin.json"
                        try:
                            plugin_data = await fetch_plugin_json(plugin_json_url)
                            plugin_data['url'] = url
                            cached_plugins.append(plugin_data)
                        except RequestError as e:
                            error_msg = f"Error fetching plugin.json for URL: {plugin_json_url}, Error: {str(e)}"
                            cached_plugins.append({"error": error_msg})

                    # Update the cache with the new data and timestamp
                    self.cache["plugins"] = cached_plugins
                    self.cache_timestamp["plugins"] = datetime.utcnow()

            except RequestError as e:
                raise HTTPException(status_code=500, detail=f"Error fetching GitHub data: {str(e)}")

        return {
            "total_plugins": len(cached_plugins),
            "page": page,
            "page_size": page_size,
            "plugins": cached_plugins,
        }

    async def get_all_tags(self):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        # Get all tags from plugin data
        all_tags = set()
        for plugin_data in self.cache["plugins"]:
            if "tags" in plugin_data:
                tags = plugin_data["tags"]
                if isinstance(tags, str):
                    all_tags.update(tags.split(","))
                elif isinstance(tags, list):
                    for tag in tags:
                        all_tags.update(tag.split(","))

        tags_dict = {i: tag.strip() for i, tag in enumerate(all_tags)}

        return tags_dict

    async def get_plugins_by_tag(self, tag_name: str, page: int = 1, page_size: int = 0):
        if page_size == 0:
            page_size = self.page_size

        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        # Find plugins containing the given tag
        matching_plugins = []
        for plugin_data in self.cache["plugins"]:
            if "tags" in plugin_data and tag_name in plugin_data["tags"]:
                matching_plugins.append(plugin_data)

        total_plugins = len(matching_plugins)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        if start_index >= total_plugins:
            return []

        return {
            "total_plugins": total_plugins,
            "page": page,
            "page_size": page_size,
            "plugins": matching_plugins[start_index:end_index],
        }

    @staticmethod
    def filter_plugins_by_names(plugins, excluded):
        return [plugin_data for plugin_data in plugins if plugin_data.get('name') not in excluded]

    async def exclude_plugins(self, page: int = 1, page_size: int = 10, excluded: List[str] = Body(..., embed=True)):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        plugins_to_exclude = set(excluded)
        filtered_plugins = self.filter_plugins_by_names(self.cache["plugins"], plugins_to_exclude)

        total_plugins = len(filtered_plugins)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        if start_index >= total_plugins:
            return []

        return {
            "total_plugins": total_plugins,
            "page": page,
            "page_size": page_size,
            "plugins": filtered_plugins[start_index:end_index],
        }

    async def get_plugins_by_author(self, author_name: str = Body(..., embed=True), page: int = 1, page_size: int = 0):
        if page_size == 0:
            page_size = self.page_size

        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        # Find plugins by the specified author name
        matching_plugins = []
        for plugin_data in self.cache["plugins"]:
            if plugin_data.get("author_name") == author_name:
                matching_plugins.append(plugin_data)

        total_plugins = len(matching_plugins)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        if start_index >= total_plugins:
            return []

        return {
            "total_plugins": total_plugins,
            "page": page,
            "page_size": page_size,
            "plugins": matching_plugins[start_index:end_index],
        }

    async def download_plugin_zip(self, plugin_data: dict):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        plugin_name = plugin_data.get("plugin_name")
        if not plugin_name:
            raise HTTPException(status_code=400, detail="Missing 'plugin_name' in request body.")

        matching_plugins = [plugin for plugin in self.cache["plugins"] if plugin.get("name") == plugin_name]

        if not matching_plugins:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")

        plugin_data = matching_plugins[0]
        plugin_url = plugin_data.get("url")

        repo_path = await self.clone_repository(plugin_url, plugin_name)

        zip_filename = await self.create_plugin_zip(repo_path, plugin_name)

        # Set the appropriate headers to trigger a download
        headers = {
            "Content-Disposition": f"attachment; filename={plugin_name}.zip"
        }

        return FileResponse(zip_filename, headers=headers, media_type="application/zip")

    @staticmethod
    async def clone_repository(plugin_url: str, plugin_name: str):
        # Define a cache directory
        cache_dir = "repository_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        repo_path = os.path.join(cache_dir, plugin_name)

        # Check if the repository is already cloned and updated
        if os.path.exists(repo_path):
            try:
                repo = git.Repo(repo_path)
                origin = repo.remotes.origin
                origin.fetch()
                
                if ("master" in origin.refs):
                    origin_master = origin.refs["master"]
                else:
                    origin_master = origin.refs["main"]
                
                diff = repo.git.diff(origin_master.commit,repo.head.commit)
                
                
                if diff == "":
                    return repo_path
                else:
                    shutil.rmtree(repo_path)
            
            except Exception as e:
                print(f"Error while checking repository status: {str(e)}")
                shutil.rmtree(repo_path)

        # Clone the repository
        try:
            git.Repo.clone_from(plugin_url, repo_path)
        except git.GitCommandError as e:
            raise HTTPException(status_code=500, detail=f"Failed to clone repository: {str(e)}")

        return repo_path

    @staticmethod
    async def create_plugin_zip(repo_path: str, plugin_name: str):
        zip_cache_dir = "zip_cache"
        if not os.path.exists(zip_cache_dir):
            os.makedirs(zip_cache_dir)

        zip_filename = os.path.join(zip_cache_dir, f"{plugin_name}.zip")

        # Create a .zip file excluding .git and __pycache__ folders
        with zipfile.ZipFile(zip_filename, "w") as zip_file:
            for root, _, files in os.walk(repo_path):
                # Skip .git and __pycache__ folders
                if ".git" in root or "__pycache__" in root:
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.relpath(file_path, repo_path))

        return zip_filename

    async def search_plugins(self, search_data: dict):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.read_remote_json()

        query = search_data.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Missing 'query' in request body.")

        query_words = query.split()

        matching_plugins = []
        for plugin_data in self.cache["plugins"]:
            plugin_matches_all_words = all(
                any(word.lower() in field.lower() for field in plugin_data.values())
                for word in query_words
            )
            if plugin_matches_all_words:
                matching_plugins.append(plugin_data)

        return matching_plugins

    @staticmethod
    async def error():
        return {'error': 'This aren\'t the plugins you are looking for!'}
