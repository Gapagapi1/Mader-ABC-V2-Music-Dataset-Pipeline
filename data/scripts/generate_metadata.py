import os
import sys

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process, verify_software_dependency


process = Process("generate_metadata", "./midi/lmd_matched_flat_sanitized", "./midi/lmd_matched_flat_metadata")


def path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".mid", ".json")

job_args = []
def process_function(from_path: str, to_path: str):
    job_args.append((from_path if os.name == "posix" else from_path.replace("/", "\\"), to_path if os.name == "posix" else to_path.replace("/", "\\")))

process.step_by_function(process_function, path_converter, folder_exist_ok=True, file_exist_ok=True)


musescore_path = verify_software_dependency(os.path.join("musescore", "MuseScore4.exe" if os.name == "nt" else "musescore"))
musescore_path = musescore_path if os.name == "posix" else musescore_path.replace('/', '\\')

command = musescore_path + " {} --score-meta"

process.step_by_popen(command, job_args, [bytearray(), bytearray()], False, True, 10, True, 1)
