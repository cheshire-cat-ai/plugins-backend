import httpx
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

GITHUB_PLUGINS_JSON_URL = "https://raw.githubusercontent.com/cheshire-cat-ai/awesome-plugins/main/plugins.json"
DEFAULT_PAGE_SIZE = 10


async def fetch_plugin_json(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


@app.get("/plugins")
async def read_remote_json(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GITHUB_PLUGINS_JSON_URL)
            data = response.json()

            total_plugins = len(data)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size

            if start_index >= total_plugins:
                return []

            plugin_json_data = []
            for entry in list(data.values())[start_index:end_index]:
                url = entry["url"]
                plugin_json_url = url.replace("github.com", "raw.githubusercontent.com") + "/main/plugin.json"
                try:
                    plugin_data = await fetch_plugin_json(plugin_json_url)
                    plugin_json_data.append(plugin_data)
                except httpx.RequestError as e:
                    error_msg = f"Error fetching plugin.json for URL: {plugin_json_url}, Error: {str(e)}"
                    plugin_json_data.append({"error": error_msg})

            return {
                "total_plugins": total_plugins,
                "page": page,
                "page_size": page_size,
                "plugins": plugin_json_data,
            }

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching GitHub data: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
