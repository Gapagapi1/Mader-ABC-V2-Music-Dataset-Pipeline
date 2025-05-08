import os
import sys

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process, verify_software_dependency

def path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".midi", ".mid")

job_args = []
def process_function(from_path: str, to_path: str):
    job_args.append((from_path if os.name == "posix" else from_path.replace("/", "\\"), to_path if os.name == "posix" else to_path.replace("/", "\\")))


if __name__ == "__main__":
    process = Process("sanitize_midi", "./midi/lmd_matched_flat", "./midi/lmd_matched_flat_sanitized")
    process.step_by_function(process_function, path_converter, folder_exist_ok=True, file_exist_ok=True)

    musescore_path = verify_software_dependency(os.path.join("musescore", "MuseScore4.exe" if os.name == "nt" else "musescore"))
    musescore_path = musescore_path if os.name == "posix" else musescore_path.replace('/', '\\')

    command = musescore_path + " {} -o {}"

    process.step_by_popen(command, job_args, [bytearray(), bytearray()], True, True, 10)
