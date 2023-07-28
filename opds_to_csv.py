import pandas as pd
from pathlib import Path
import json
import csv

from collections import MutableMapping


def flatten(dictionary: Dict[str, Any], parent_key: Otional[str] = None, separator: str = '.'):
    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            if not value.items():
                items.append((new_key,None))
            else:
                items.extend(flatten(value, new_key, separator).items())
        elif isinstance(value, list):
            if len(value):
                for k, v in enumerate(value):
                    items.extend(flatten({str(k): v}, new_key, separator).items())
            else:
                items.append((new_key,None))
        else:
            items.append((new_key, value))
    return dict(items)


# Set path to file
p = Path("combined.json")

# Open file
with p.open('r', encoding='utf-8') as f:
    data = json.loads(f.read())

flattened = [flatten(d) for d in data]

# create dataframe
df = pd.json_normalize(flattened)

# save to csv
df.to_csv('test.csv', index=False, encoding='utf-8')