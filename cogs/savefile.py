import json
import os
import pathlib

def get_save_file_value(file):
    path = pathlib.Path(__file__)
    path = f"{path.parent.parent}{os.sep}files{os.sep}{file}"
    with open(path, mode='r') as file:
        return json.loads(file.read())