import os
import json
import threading

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
