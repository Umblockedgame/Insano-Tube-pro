import json
import re
import urllib.parse
import requests
from .lt_misc import *


def get_channel_data(channel_url):
    """
    Esta función extrae datos sobre un canal de YouTube
    """
    # Enviar solicitud para obtener el contenido de la página
    url = f"https://www.youtube.com/channel/{channel_url}/videos"
    r = requests.get(url, headers=headers, cookies=cookies)
    r.raise_for_status()

    # Extraer los datos necesarios de la página
    page_data = json.loads(
        re.search(r"ytInitialData\s*=\s*({.*?});", r.text).group(1))

    channeldata = {
        "channel_name": "",
        "subscriberCount": "",
        "videosCount": "",
        "channel_profile_picture": "",
        "channel_banner": "",
        "channel_description": "",
        "isVerified": False,
        "videos": [],
        "key": None,
        "continuationtoken": None
    }

    try:
        channeldata_metadata = page_data["metadata"]["channelMetadataRenderer"]
        channeldata["channel_name"] = channeldata_metadata["title"]
        channeldata["channel_profile_picture"] = channeldata_metadata["avatar"]["thumbnails"][0] if "avatar" in channeldata_metadata else ""
        channeldata["channel_description"] = channeldata_metadata.get(
            "description", "")
    except KeyError as e:
        print(f"Metadata extraction error: {e}")

    try:
        if "c4TabbedHeaderRenderer" in page_data["header"]:
            channeldata_header = page_data["header"]["c4TabbedHeaderRenderer"]
        # Suponer que podría haber otro tipo de encabezado
        elif "someOtherHeaderRenderer" in page_data["header"]:
            channeldata_header = page_data["header"]["someOtherHeaderRenderer"]
        else:
            raise KeyError("No suitable header renderer found")

        channeldata["subscriberCount"] = channeldata_header["subscriberCountText"]["simpleText"]
        channeldata["videosCount"] = channeldata_header["videosCountText"]["runs"][0]["text"]
        channeldata["channel_banner"] = channeldata_header["banner"]["thumbnails"][-1] if "banner" in channeldata_header else ""
        channeldata["isVerified"] = channeldata_header["badges"][0]["metadataBadgeRenderer"][
            "tooltip"] == "Verified" if channeldata_header.get("badges") else False
    except KeyError as e:
        print(f"Header extraction error: {e}")

    # Extraer datos sobre los videos
    try:
        for video in page_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"]["richGridRenderer"]["contents"]:
            try:
                video_data = {
                    "id": video["richItemRenderer"]["content"]["videoRenderer"]["videoId"],
                    "views": human_format(video["richItemRenderer"]["content"]["videoRenderer"]["viewCountText"]["simpleText"]),
                    "published": video["richItemRenderer"]["content"]["videoRenderer"]["publishedTimeText"]["simpleText"],
                    "thumbnail": video["richItemRenderer"]["content"]["videoRenderer"]["thumbnail"]["thumbnails"][0]["url"],
                    "title": video["richItemRenderer"]["content"]["videoRenderer"]["title"]["runs"][0]["text"],
                }
                channeldata["videos"].append(video_data)
            except KeyError:
                pass
    except KeyError as e:
        print(f"Video extraction error: {e}")

    # Extraer la clave y el token de continuación para la paginación
    try:
        channeldata["key"] = re.search(
            r'"INNERTUBE_API_KEY":"(.*?)"', r.text).group(1)
    except AttributeError:
        channeldata["key"] = None

    try:
        channeldata["continuationtoken"] = re.search(
            r'"continuationCommand":{"token":"(.*?)"', r.text).group(1)
    except AttributeError:
        channeldata["continuationtoken"] = None

    return channeldata
