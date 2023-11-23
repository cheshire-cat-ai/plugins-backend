import os
import json
import threading
import pandas as pd
import plotly.express as px
import base64

# Lock file for avoid concurrency issues
file_lock = threading.Lock()


def get_analytics():
    try:
        # Acquire the lock before accessing the file
        with file_lock:
            analytics_file = "analytics.json"

            analytics_data = {}

            if os.path.exists(analytics_file):
                with open(analytics_file, "r") as file:
                    analytics_data = json.load(file)

            return analytics_data
    finally:
        pass


def update_analytics(url):
    try:
        analytics_data = get_analytics()

        if url in analytics_data:
            analytics_data[url] += 1
        else:
            analytics_data[url] = 1

        with file_lock:
            analytics_file = "analytics.json"
            with open(analytics_file, "w") as file:
                json.dump(analytics_data, file, indent=4)
    finally:
        # Release the lock when done to allow other requests to access the file
        if file_lock.locked():
            file_lock.release()


def generate_plot(plugins):
    analytics = get_analytics()
    df = pd.DataFrame({
        "plugin": list(analytics.keys()),
        "downloads": list(analytics.values()),
    })

    df = df.sort_values("downloads", ascending=True)

    url_to_name = {entry['url']: entry['name'] for entry in plugins}
    df["plugin"] = df["plugin"].map(url_to_name)

    fig = px.bar(df, y="plugin", x="downloads", orientation='h')
    fig.update_layout(
        title='<b>Downloads by Plugin</b>',
        xaxis_title='<b>Number of Downloads</b>',
        yaxis_title='<b>Plugin</b>',
        font=dict(size=14, family='Open Sans', color='black'),
        title_font=dict(size=18, family='Open Sans', color='black'),
        xaxis=dict(showgrid=True, gridcolor='grey'),
        height=600,
        width=1024
    )
    fig.update_traces(
        marker=dict(line=dict(width=1, color='DarkSlateGrey')),
        opacity=0.9,
        marker_color='cornflowerblue',
        marker_line_color='black'
    )

    img_bytes = fig.to_image(format="png")

    # Encode the image bytes to base64 so we can pass it as html
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    html_img = f'<img src="data:image/png;base64,{img_base64}" />'

    return html_img
