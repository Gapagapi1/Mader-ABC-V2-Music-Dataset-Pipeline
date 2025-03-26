import os
import sys
import json
import shutil

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process

wrong_abc_files = []

def wrong_abc(from_path: str, reason:str):
    wrong_abc_files.append({"path": from_path, "reason": reason})
    print("[clean_abc]", from_path, "is a wrong abc file:", reason)

def process_function(from_path: str, to_path: str):
    with open(from_path, 'r') as abc_file:
        is_empty = True
        found_M_statement = False

        while line := abc_file.readline():
            is_empty = False

            if line.startswith("M"):
                found_M_statement = True
                break

        if is_empty:
            wrong_abc(from_path, "empty file ({})".format(abc_file.read()))
            return

        if not found_M_statement:
            wrong_abc(from_path, "M statement not found")
            return

        if line.startswith("M: -"):
            wrong_abc(from_path, "M statement is negative ({})".format(line.strip("\n")))
            return

        shutil.copy2(from_path, to_path)


process = Process("clean_abc", "./midi/lmd_matched_flat_sanitized_abc", "./midi/lmd_matched_flat_sanitized_abc_clean")
process.step_by_function(process_function)

with open("./results/failed_jobs_{}.json".format("clean_abc"), "w") as wrong_file:
    json.dump(wrong_abc_files, wrong_file)