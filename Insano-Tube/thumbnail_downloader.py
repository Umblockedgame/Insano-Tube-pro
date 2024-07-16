import os
import requests


def download_thumbnail(video_id):
    url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    response = requests.get(url, stream=True, timeout=10)
    if response.status_code == 200:
        thumbnail_path = f"static/thumbnails/{video_id}.jpg"
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        with open(thumbnail_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return thumbnail_path
    else:
        return None
