from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import requests
from alive_progress import alive_bar
from requests import Session

# Production and testing have different host names for some of the
# API endpoints. This is configurable on the collection level.
HOSTS = {
    "production": dict(
        host="https://api.overdrive.com",
        oauth_host="https://oauth.overdrive.com",
    ),
    "testing": dict(
        host="https://integration.api.overdrive.com",
        oauth_host="https://oauth.overdrive.com",
    ),
}

TOKEN_ENDPOINT = "%(oauth_host)s/token"
EVENTS_ENDPOINT = "%(host)s/v1/collections/%(collection_token)s/products?sort=%(sort)s&limit=%(limit)s"
LIBRARY_ENDPOINT = "%(host)s/v1/libraries/%(library_id)s"
ADVANTAGE_LIBRARY_ENDPOINT = (
    "%(host)s/v1/libraries/%(parent_library_id)s/advantageAccounts/%(library_id)s"
)


def handle_error(resp: requests.Response) -> None:
    if resp.status_code == 200:
        return
    print(f"Error: {resp.status_code}")
    print(f"Headers: {json.dumps(dict(resp.headers), indent=4)}")
    print(resp.text)
    sys.exit(-1)


def get_auth_token(host: str, client_key: str, client_secret: str) -> str:
    endpoint = TOKEN_ENDPOINT % HOSTS[host]
    auth = (client_key, client_secret)
    resp = requests.post(
        endpoint, auth=auth, data=dict(grant_type="client_credentials")
    )
    handle_error(resp)
    return resp.json()["access_token"]  # type: ignore[no-any-return]


def get_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + auth_token, "User-Agent": "Palace"}


def get_collection_token(
    session: Session, host: str, library_id: str, parent_library_id: str | None
) -> str:
    if parent_library_id:
        endpoint = ADVANTAGE_LIBRARY_ENDPOINT % {
            "host": HOSTS[host]["host"],
            "parent_library_id": parent_library_id,
            "library_id": library_id,
        }
    else:
        endpoint = LIBRARY_ENDPOINT % {
            "host": HOSTS[host]["host"],
            "library_id": library_id,
        }
    resp = session.get(endpoint)
    handle_error(resp)
    return resp.json()["collectionToken"]  # type: ignore[no-any-return]


def first_event_url(host: str, collection_token: str) -> str:
    return EVENTS_ENDPOINT % {
        "host": HOSTS[host]["host"],
        "collection_token": collection_token,
        "sort": "popularity:desc",
        "limit": 200,
    }


def get_events(
    url: str,
    session: Session,
    fetch_metadata: bool = False,
    fetch_availability: bool = False,
    bar: Callable[[], None] | None = None,
) -> tuple[dict[str, Any], str | None]:
    resp = session.get(url)
    handle_error(resp)
    response_data = resp.json()
    next_url = get_next_url(response_data)

    if bar:
        bar()

    if fetch_metadata:
        for product in response_data["products"]:
            metadata = session.get(product["links"]["metadata"]["href"])
            handle_error(metadata)
            product["metadata"] = metadata.json()
            if bar:
                bar()

    if fetch_availability:
        for product in response_data["products"]:
            availability = session.get(product["links"]["availability"]["href"])
            handle_error(availability)
            product["availability"] = availability.json()
            if bar:
                bar()

    return response_data, next_url


def get_next_url(events: dict[str, Any]) -> str | None:
    if "links" not in events:
        return None
    if "next" not in events["links"]:
        return None
    return events["links"]["next"]["href"]  # type: ignore[no-any-return]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="download_overdrive", description="Download Overdrive feed"
    )

    parser.add_argument("output_file", help="Output file")
    parser.add_argument("-k", "--client-key", help="Client Key", required=True)
    parser.add_argument("-s", "--client-secret", help="Client Secret", required=True)
    parser.add_argument("-l", "--library-id", help="Library ID", required=True)
    parser.add_argument(
        "-p", "--parent-library-id", help="Parent Library ID (for Advantage Accounts)"
    )
    parser.add_argument("-q", "--qa", help="Use QA Endpoint", action="store_true")
    parser.add_argument("-m", "--metadata", help="Fetch metadata", action="store_true")
    parser.add_argument(
        "-a", "--availability", help="Fetch availability", action="store_true"
    )

    # Get args from command line
    args = parser.parse_args()

    host = "testing" if args.qa else "production"

    # Create a session to fetch the documents
    session = requests.Session()

    # Get the auth token
    auth_token = get_auth_token(host, args.client_key, args.client_secret)
    session.headers.update(get_headers(auth_token))

    # Get the collection token
    collection_token = get_collection_token(
        session, host, args.library_id, args.parent_library_id
    )

    # Get first page of events
    url = first_event_url(host, collection_token)
    events, _ = get_events(url, session, False, False)

    products = []

    # Figure out how many pages there are
    items = events["totalItems"]
    items_per_page = events["limit"]
    pages = math.ceil(items / items_per_page)
    fetches = (
        pages + (items if args.metadata else 0) + (items if args.availability else 0)
    )

    next_url: str | None = url
    with alive_bar(fetches, file=sys.stderr) as bar:
        while next_url is not None:
            events, next_url = get_events(
                next_url, session, args.metadata, args.availability, bar
            )
            products.extend(events["products"])

    with Path(args.output_file).open("w") as file:
        file.write(json.dumps(products, indent=4))
