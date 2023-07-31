# download_opds.py

## About

This script downloads an OPDS 2 feed and saves it to a file. The script will crawl the feed and download all the
entries. It will either output all the entries as a large JSON file, or flatten the json and output a CSV file.

## Installation

This script requires Python 3.9 or later and https://python-poetry.org/.

If you don't have these requirements, and are using OSX, you can install them with [Homebrew](https://brew.sh/).

```bash
brew install pyenv
brew install poetry
```

Once you have the requirements, you can install the dependencies with:

```bash
poetry install
```

## Usage

```bash
usage: download_opds [-h] [-u USERNAME] [-p PASSWORD] [-c] url output_file

Download OPDS 2 feed

positional arguments:
  url                   URL of feed
  output_file           Output file

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Username
  -p PASSWORD, --password PASSWORD
                        Password
  -c, --csv             Output CSV file
```
