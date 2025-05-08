import os
import sys

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process


def path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".abc", "")

def process_function(from_path: str, to_path: str):
    try:
        os.makedirs(to_path, exist_ok=True)

        with open(from_path, 'r') as abc_file:
            lines = abc_file.readlines()

        track_data = {}
        track = 0
        header = ""

        for line in lines:
            if line.replace(" ", "").startswith("V:"):
                track += 1
                track_data[track] = [header]
                continue

            if track == 0:
                header += line
            else:
                track_data[track].append(line)

        for track_num, data in track_data.items():
            track_path = os.path.join(to_path, f"track {track_num}.abc")
            with open(track_path, 'w') as f:
                f.writelines(data)
    except Exception as e:
        import traceback
        print(f"[Process Function Error] Failed for {from_path} -> {to_path} with exception \"{e}\": " + traceback.format_exc())
        raise


if __name__ == "__main__":
    process = Process("split_abc_tracks", "./midi/lmd_matched_flat_sanitized_abc_clean", "./midi/lmd_matched_flat_sanitized_abc_clean_split")
    process.step_by_function(process_function, path_converter, useProcessExecutor=True)
