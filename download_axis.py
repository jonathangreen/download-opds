import argparse
import base64
import json
import sys
from typing import Dict
from xml.dom import minidom

import requests
import xmltodict

PRODUCTION_BASE_URL = "https://axis360api.baker-taylor.com/Services/VendorAPI/"
QA_BASE_URL = "https://axis360apiqa.baker-taylor.com/Services/VendorAPI/"

access_token_endpoint = "accesstoken"
availability_endpoint = "availability/v2"


def get_headers(
    base_url: str, username: str, password: str, library_id: str
) -> Dict[str, str]:
    authorization_str = ":".join([username, password, library_id])
    authorization_bytes = authorization_str.encode("utf_16_le")
    authorization_b64 = base64.standard_b64encode(authorization_bytes)
    resp = requests.post(
        base_url + access_token_endpoint,
        headers={"Authorization": b"Basic " + authorization_b64},
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code}")
        print(f"Headers: {json.dumps(dict(resp.headers), indent=4)}")
        print(resp.text)
        sys.exit(-1)
    return {
        "Authorization": "Bearer " + resp.json()["access_token"],
        "Library": library_id,
    }


def availability(base_url: str, username: str, password: str, library_id: str) -> str:
    headers = get_headers(base_url, username, password, library_id)
    resp = requests.get(
        base_url + availability_endpoint,
        headers=headers,
        params={"updatedDate": "1970-01-01 00:00:00"},
    )
    return resp.text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="download_axis", description="Download B&T Axis 360 feed"
    )

    parser.add_argument("output_file", help="Output file")
    parser.add_argument("-u", "--username", help="Username", required=True)
    parser.add_argument("-p", "--password", help="Password", required=True)
    parser.add_argument("-l", "--library-id", help="Library ID", required=True)
    parser.add_argument("-j", "--json", help="Output JSON file", action="store_true")
    parser.add_argument("-q", "--qa", help="Use QA Endpoint", action="store_true")

    # Get args from command line
    args = parser.parse_args()

    # Find the base URL to use
    base_url = PRODUCTION_BASE_URL if not args.qa else QA_BASE_URL

    # Fetch the document as XML
    xml = availability(base_url, args.username, args.password, args.library_id)

    if args.json:
        xml_dict = xmltodict.parse(xml)
        with open(args.output_file, "w") as file:
            file.write(json.dumps(xml_dict, indent=4))
    else:
        parsed = minidom.parseString(xml)
        with open(args.output_file, "w") as file:
            file.write(parsed.toprettyxml())
