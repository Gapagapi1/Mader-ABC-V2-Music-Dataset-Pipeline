import json
import os
import sys

sys.path.append("./scripts")
print(sys.path)
from data_pipeline_lib import Process

wrong_metadata_files = []

def process_function(from_path: str, to_path: str):
    try:
        with open(from_path, 'r') as metadata_file:
            json.load(metadata_file)
    except Exception as e:
        print(from_path, "is a wrong metadata file:", e)

process = Process("verify_metadata", "./midi/lmd_matched_flat_metadata", "./midi/lmd_matched_flat_metadata_tmp")
process.step_by_function(process_function)

os.removedirs("./midi/lmd_matched_flat_metadata_tmp")

with open("./results/failed_jobs_{}.json".format("verify_metadata"), "w") as wrong_file:
    json.dump(wrong_metadata_files, wrong_file)
