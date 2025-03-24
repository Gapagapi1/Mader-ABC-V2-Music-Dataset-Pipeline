import os
import sys

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process


def path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".abc", "")

def process_function(from_path: str, to_path: str):
    os.makedirs(to_path, exist_ok=True)

    with open(from_path, 'r') as abc_file:
        lines = abc_file.readlines()

    track = 0

    header = ""

    for line in lines:
        track_path = os.path.join(to_path, "track {}.abc".format(track))

        if line.startswith("V:"):
            track += 1
            track_path = os.path.join(to_path, "track {}.abc".format(track))
            with open(track_path, 'a') as split_abc_file:
                split_abc_file.write(header)
            continue

        if track == 0:
            header += line
            continue

        with open(track_path, 'a') as split_abc_file:
            split_abc_file.write(line)


process = Process("split_abc_tracks", "./midi/lmd_matched_flat_sanitized_abc_clean", "./midi/lmd_matched_flat_sanitized_abc_clean_split")
process.step_by_function(process_function, path_converter, status_update_time_delta_threshold=0.001)