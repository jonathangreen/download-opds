import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, Any

import requests
from alive_progress import alive_bar
from requests import Session


def make_request(session: Session, url: str) -> Dict[str, Any]:
    response = session.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(-1)
    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='download_opds',
                    description='Download OPDS 2 feed')

    parser.add_argument('url', help='URL of feed')
    parser.add_argument('-u', '--username', help='Username')
    parser.add_argument('-p', '--password', help='Password')
    parser.add_argument('-o', '--output', help='Output file')

    # Get args from comand line
    args = parser.parse_args()

    # Create a session to fetch the documents
    session = requests.Session()

    if args.username and args.password:
        session.auth = (args.username, args.password)

    session.headers.update({'Accept': 'application/opds+json'})

    publications = []

    # Get the first page
    response = make_request(session, args.url)
    items = response["metadata"]["numberOfItems"]
    items_per_page = response["metadata"]["itemsPerPage"]
    pages = math.ceil(items/items_per_page)

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

    if args.output:
        with Path(args.output).open('w') as file:
            file.write(json.dumps(publications, indent=4))
    else:
        print(json.dumps(publications, indent=4))
