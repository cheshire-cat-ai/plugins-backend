from urllib.parse import urlparse
from fastapi import HTTPException, APIRouter, Body
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi
from httpx import AsyncClient, RequestError
from utils import *
from typing import List, Dict, Optional
from logger import error_log
from analytics import update_analytics, generate_plot
import os
from plugins_html_table import generate_plugins_html_table, PLUGIN_COLUMNS
import shutil
import git
import zipfile


class Endpoints:

    def __init__(self, app, plugin_json, cache_duration, page_size):
        self.cache_duration = cache_duration
        self.json = plugin_json
        self.page_size = page_size
        self.app = app
        self.cache = {}
        self.cache_timestamp = {}
        # Define FastAPI endpoints
        self.router = APIRouter()
        self.router.add_api_route("/plugins", self.get_all_plugins, methods=["GET"])
        self.router.add_api_route("/plugins_table", self.get_plugins_html_table, methods=["GET"])
        self.router.add_api_route("/tags", self.get_all_tags, methods=["GET"])
        self.router.add_api_route("/tag/{tag_name}", self.get_plugins_by_tag, methods=["GET"])
        self.router.add_api_route("/exclude", self.exclude_plugins, methods=["POST"])
        self.router.add_api_route("/author", self.get_plugins_by_author, methods=["POST"])
        self.router.add_api_route("/download", self.download_plugin_zip, methods=["POST"])
        self.router.add_api_route("/search", self.search_plugins, methods=["POST"])
        self.router.add_api_route("/analytics", self.get_analytics, methods=["GET"])
        self.router.add_api_route("/analytics/graph", self.get_analytics_plot, methods=["GET"])
        self.router.add_api_route("/", self.home, methods=["GET"])
        app.include_router(self.router)

    async def cache_plugins(self):
        try:
            async with AsyncClient() as client:
                response = await client.get(self.json)
                data = response.json()
                analytics_data = read_analytics_data()

                cached_plugins = []
                for entry in data:
                    url = entry["url"]
                    plugin_json_url = url.replace("github.com", "raw.githubusercontent.com") + "/main/plugin.json"
                    try:
                        print(f"Fetching plugin {plugin_json_url}")
                        plugin_data = await fetch_plugin_json(plugin_json_url)

                        # Validate plugin.json required fields
                        name = plugin_data.get("name")
                        author_name = plugin_data.get("author_name")
                        if name and author_name:
                            plugin_data['url'] = url
                            cached_plugins.append(plugin_data)
                        else:
                            message = f"Error: Skipping plugin {url}"
                            error_log(message, "WARNING")
                    except Exception as e:
                        error_msg = f"Error fetching plugin: {plugin_json_url}, Error: {str(e)}"
                        error_log(error_msg, "ERROR")

                for plugin in cached_plugins:
                    # Use the 'url' from the item to find the corresponding analytics data
                    downloads = analytics_data.get(plugin['url'])
                    # If analytics data is found, add a 'downloads' key to the item with the value
                    if downloads is not None:
                        plugin['downloads'] = downloads
                    else:
                        # noinspection PyTypeChecker
                        plugin['downloads'] = 0

                # Update the cache with the new data and timestamp
                self.cache["plugins"] = cached_plugins
                self.cache_timestamp["plugins"] = datetime.utcnow()

        except RequestError as e:
            message = f"Error fetching data from GitHub: {str(e)}"
            error_log(f"Can't cache plugins. {message}", "ERROR")
            raise HTTPException(status_code=500, detail=message)

    async def get_all_plugins(self, page: int = 1, page_size: int = 0, order: Optional[str] = None):
        if page_size == 0:
            page_size = self.page_size

        # Check if cache is still valid
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.cache_plugins()

        # Retrieve plugins from cache
        cached_plugins = self.cache["plugins"]

        # Create a copy for preserving the original order
        sorted_plugins = cached_plugins[:]

        if order == 'oldest':
            pass  # Default
        elif order == 'newest':
            sorted_plugins = list(reversed(sorted_plugins))
        elif order == 'popular':
            sorted_plugins.sort(key=lambda x: x.get('downloads', 0), reverse=True)
        elif order == 'a2z':
            sorted_plugins.sort(key=lambda x: x.get('name', '').lower())
        elif order == 'z2a':
            sorted_plugins.sort(key=lambda x: x.get('name', '').lower(), reverse=True)

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_plugins = sorted_plugins[start_index:end_index]

        return {
            "total_plugins": len(sorted_plugins),
            "page": page,
            "page_size": page_size,
            "plugins": paginated_plugins,
        }
    
    async def get_plugins_html_table(self, columns: Optional[str] = ",".join(PLUGIN_COLUMNS), render_link: Optional[bool] = False, classes: Optional[str] = "plugins-table"):
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.cache_plugins()

        html_img = generate_plugins_html_table(self.cache["plugins"], columns, render_link, classes)
        return HTMLResponse(content=html_img)

    async def get_all_tags(self):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.cache_plugins()

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
            await self.cache_plugins()

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
            await self.cache_plugins()

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
            await self.cache_plugins()

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

    @staticmethod
    async def get_analytics() -> Dict[str, int]:
        analytics_data = read_analytics_data()
        return analytics_data

    async def get_analytics_plot(self) -> HTMLResponse:
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.cache_plugins()

        html_img = generate_plot(self.cache["plugins"])
        return HTMLResponse(content=html_img)

    async def download_plugin_zip(self, plugin_data: dict = Body({"url": ""})):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.cache_plugins()

        plugin_url = plugin_data.get("url")
        if not plugin_url:
            raise HTTPException(status_code=400, detail="Missing 'url' in request body.")

        matching_plugins = [plugin for plugin in self.cache["plugins"] if plugin.get("url") == plugin_url]

        if not matching_plugins:
            raise HTTPException(status_code=404, detail=f"Plugin url '{plugin_url}' not found.")

        plugin_data = matching_plugins[0]
        plugin_name = str(plugin_data.get("name"))

        # Check if there is a release zip file
        path_url = str(urlparse(plugin_url).path)
        url = "https://api.github.com/repos" + path_url + "/releases"

        async with AsyncClient() as client:

            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail={"error": "Github API not available"}
                )
            response = response.json()
            
            i = 0
            try:
                # list of assets with files differents from Source code zips
                assets = response[i]["assets"]
                while len(assets) == 0:
                    i += 1
                    assets = response[i]["assets"]

                url_zip = assets[0]["browser_download_url"]
                version = response[i]["tag_name"]
                if i != 0:
                    error_log(f"The plugin {plugin_name} has no release zip file or was pushed by hand, the version pulled is {version}", "WARNING")

                zip_filename = await self.download_releses_plugin_zip(plugin_name, url_zip, version)
            except (IndexError, KeyError):
                # if you are here, there aren't any assets in the response. So, download the zip repo
                repo_path = await self.clone_repository(plugin_url, plugin_name)
                zip_filename = await self.create_plugin_zip(repo_path, plugin_name)

        # Set the appropriate headers to trigger a download
        headers = {
            "Content-Disposition": f"attachment; filename={plugin_name}.zip"
        }

        # Update analytics count
        update_analytics(plugin_url)

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

                if "master" in origin.refs:
                    origin_master = origin.refs["master"]
                else:
                    origin_master = origin.refs["main"]

                diff = repo.git.diff(origin_master.commit, repo.head.commit)

                if diff == "":
                    return repo_path
                else:
                    shutil.rmtree(repo_path)

            except Exception as e:
                message = f"Error while checking repository status: {str(e)}"
                error_log(f"{repo_path} - {message}", "WARNING")
                shutil.rmtree(repo_path)

        # Clone the repository
        try:
            git.Repo.clone_from(plugin_url, repo_path)
        except git.GitCommandError as e:
            message = f"Failed to clone repository: {str(e)}"
            error_log(f"{repo_path} - {message}")
            raise HTTPException(status_code=500, detail=message)

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

    @staticmethod
    async def download_releses_plugin_zip(plugin_name: str, url_zip: str, version_origin: str):
        # Define a cache directory
        cache_dir = "zip_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        name_plugin = plugin_name + ".zip"
        os_path_plugin = os.path.join(cache_dir, name_plugin)

        check = check_version_zip(plugin_name, version_origin)

        if os.path.exists(os_path_plugin) and check:
            return os_path_plugin
        else:
            async with httpx.AsyncClient() as client:
                response = await client.get(url_zip)

                """
                Check if there is a redirect, by looping the response
                """
                while response.is_redirect:
                    try:
                        url_location = response.headers["location"]
                        response = await client.get(url_location)
                    except httpx.RequestError as e:
                        error = {"error": str(e)}
                        raise HTTPException(
                            status_code=400,
                            detail=error
                        )

                if response.status_code != 200:
                    error_message = f"GitHub API error: {response.text}"
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_message
                    )

                with open(os_path_plugin, "wb") as zip_ref:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        zip_ref.write(chunk)
                update_version_zip(plugin_name, version_origin)

            return os_path_plugin

    async def search_plugins(self, search_data: dict):
        # Check if cache is still valid, otherwise update the cache
        if not is_cache_valid(self.cache_duration, self.cache_timestamp):
            await self.cache_plugins()

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

    async def home(self):
        """
        Returns the registry status.
        """
        out = {
            "status": "✅ Running: Fuck the American Dream! 🖕",
            "version": self.app.openapi_schema["info"]["version"]
        }
        return out

    def customize_openapi(self, title: str, logo_url: str, version: str, description: str):
        if self.app.openapi_schema:
            return self.app.openapi_schema
        openapi_schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=self.app.routes,
        )
        openapi_schema["info"]["x-logo"] = {
            "url": logo_url
        }
        self.app.openapi_schema = openapi_schema
        return self.app.openapi_schema
