from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict

import requests
from alive_progress import alive_bar
from requests import Session


def flatten_dict(
    dictionary: Dict[str, Any], parent_key: Otional[str] = None, separator: str = "."
) -> Dict[str, str]:
    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            if not value.items():
                items.append((new_key, None))
            else:
                items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, list):
            if len(value):
                for k, v in enumerate(value):
                    items.extend(flatten_dict({str(k): v}, new_key, separator).items())
            else:
                items.append((new_key, None))
        else:
            items.append((new_key, value))
    return dict(items)


def flatten_list(data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [flatten_dict(d) for d in data]


def make_request(session: Session, url: str) -> Dict[str, Any]:
    response = session.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(-1)
    return response.json()


def write_json(file: File, data: List[Dict[str, Any]]) -> None:
    file.write(json.dumps(data, indent=4))


def write_csv(file: File, data: List[Dict[str, Any]]) -> None:
    flattened = flatten_list(data)
    df = pd.json_normalize(flattened)
    df.to_csv(file, index=False, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="download_opds", description="Download OPDS 2 feed"
    )

    parser.add_argument("url", help="URL of feed")
    parser.add_argument("output_file", help="Output file")
    parser.add_argument("-u", "--username", help="Username")
    parser.add_argument("-p", "--password", help="Password")
    parser.add_argument("-c", "--csv", help="Output CSV file", action="store_true")

    # Get args from command line
    args = parser.parse_args()

    # Create a session to fetch the documents
    session = requests.Session()

    if args.username and args.password:
        session.auth = (args.username, args.password)

    session.headers.update({"Accept": "application/opds+json"})

    publications = []

    # Get the first page
    response = make_request(session, args.url)
    items = response["metadata"]["numberOfItems"]
    items_per_page = response["metadata"]["itemsPerPage"]
    pages = math.ceil(items / items_per_page)

    # Fetch the rest of the pages:
    next_url = args.url
    with alive_bar(pages, file=sys.stderr) as bar:
        while next_url is not None:
            response = make_request(session, next_url)
            publications.extend(response["publications"])
            next_url = None
            for link in response["links"]:
                if link["rel"] == "next":
                    next_url = link["href"]
                    break
            bar()

    with Path(args.output_file).open("w") as file:
        if args.csv:
            write_csv(file, publications)
        else:
            write_json(file, publications)
