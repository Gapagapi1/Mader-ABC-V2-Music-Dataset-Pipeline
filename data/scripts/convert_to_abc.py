import os
import sys

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process, verify_software_dependency


process = Process("convert_to_abc", "./midi/lmd_matched_flat_sanitized", "./midi/lmd_matched_flat_sanitized_abc")


def path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".mid", ".abc")

job_args = []
def process_function(from_path: str, to_path: str):
    job_args.append((from_path if os.name == "posix" else from_path.replace("/", "\\"), to_path if os.name == "posix" else to_path.replace("/", "\\")))

process.step_by_function(process_function, path_converter, folder_exist_ok=True, file_exist_ok=True)


midi2abc_path = verify_software_dependency(os.path.join("abcmidi", "midi2abc.exe" if os.name == "nt" else "midi2abc"))
midi2abc_path = midi2abc_path if os.name == "posix" else midi2abc_path.replace('/', '\\')

command = midi2abc_path + " -f {} -k 0 -obpl -nogr -noly -o {}"

process.step_by_popen(command, job_args, [bytearray(), bytearray()], True, True, 10, scheduler_tick_rate=0, allocated_cores=64)