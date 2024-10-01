import pandas as pd
from fastapi import HTTPException

PLUGIN_COLUMNS = [
    "name",
    "description",
    "author_name",
    "author_url",
    "plugin_url",
    "tags",
    "thumb",
    "version",
    "url",
    "downloads"
]

def generate_plugins_html_table(plugins, columns: str = ",".join(PLUGIN_COLUMNS), render_link: bool = False, classes: str = "plugins-table"):
    splitted_columns = columns.split(",")
    for column in splitted_columns:
        if column not in PLUGIN_COLUMNS:
            raise HTTPException(status_code=406, detail=f"'column' field: {column} not valid. Valid fields: {PLUGIN_COLUMNS}")

    df = pd.DataFrame(plugins)
    df = df.filter(splitted_columns)
    return df.to_html(index=False, render_links=render_link, classes=classes)
