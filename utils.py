import requests


def example_page_format(DatabaseId, headers):
    url = f"https://api.notion.com/v1/databases/{DatabaseId}/query"
    response = requests.post(url, json={"page_size": 1}, headers=headers)
    data = response.json()
    results = data["results"][0]
    print(results["properties"])


def table_scheme(
    date, activity_type, distance, moving_time, elevation, strava_id, title
):
    data = dict()
    data["Date"] = {
        "id": "4Jv%24",
        "type": "date",
        "date": {
            "start": date["start_notion"],
            "end": date["end_notion"],
            "time_zone": None,
        },
    }
    data["Type"] = {"id": "5Jv%24", "type": "select",
                    "select": {"name": activity_type}}
    data["Distance (m)"] = {"id": "6Jv%24",
                            "type": "number", "number": distance}
    data["Time (s)"] = {"id": "7Jv%24",
                        "type": "number", "number": moving_time}
    data["Elevation (m)"] = {"id": "kM~R",
                             "type": "number", "number": elevation}
    data["Strava_ID"] = {"id": "lkW%7D", "type": "number", "number": strava_id}
    data["Name"] = {
        "id": "title",
        "type": "title",
        "title": [
            {
                "type": "text",
                "text": {"content": title, "link": None},
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default",
                },
                "plain_text": title,
                "href": None,
            }
        ],
    }
    return data


def create_page(
    headers, DatabaseId, data: dict, icon: str = None, cover_url: str = None
):
    create_url = "https://api.notion.com/v1/pages"

    if icon != None:
        icon = {"type": "emoji", "emoji": icon}

    if cover_url != None:
        cover_url = {"type": "external", "external": {"url": cover_url}}

    payload = {
        "parent": {"database_id": DatabaseId},
        "cover": cover_url,
        "icon": icon,
        "properties": data,
    }

    res = requests.post(create_url, headers=headers, json=payload)
    if res.status_code != 200:
        print(f"{res.status_code}: Error during page creation")
        return None
    return res
