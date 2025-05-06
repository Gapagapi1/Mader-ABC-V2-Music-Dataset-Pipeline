import os
import sys
import json
import shutil
import music21

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process, verify_software_dependency

wrong_abc_files = {}

def wrong_abc(from_path: str, reason:str):
    wrong_abc_files.update({from_path: reason})
    print("[clean_abc]", from_path, "is a wrong abc file:", reason)


def get_metadata_from_midi_path(input_path: str) -> str | None:
    parts = input_path.split(os.sep)

    if len(parts) < 3 or not parts[-1].endswith('.abc'):
        return None

    return os.sep.join(parts[:-3] + ['lmd_matched_flat_metadata', parts[-2], os.path.splitext(parts[-1])[0] + '.json'])

def process_function(from_path: str, to_path: str):
    with open(from_path) as abc_file:
        data = abc_file.read()

    M_declaration = data.find("M: ")

    if M_declaration == -1:
        wrong_abc(from_path, "no M declaration")
        return
    elif "-" == data[M_declaration + 3]:
        wrong_abc(from_path, "M declaration is negative")
        return

    K_declaration = data.find("K:C ")

    if K_declaration == -1:
        wrong_abc(from_path, "K declaration is not C")
        return

    try:
        abc = music21.abcFormat.ABCHandler()
        abc.process(data)

        if not abc.definesMeasures():
            wrong_abc(from_path, "not measures defined")
            return

        if not abc.hasNotes():
            wrong_abc(from_path, "has no notes")
            return

        metadata_path = get_metadata_from_midi_path(from_path)

        if metadata_path == None:
            wrong_abc(from_path, "could not create associated metadata path")
            return

        if not os.path.exists(metadata_path):
            wrong_abc(from_path, "metadata path does not exist")
            return

        with open(metadata_path, "r") as metadata_file:
            metadata = json.load(metadata_file)

        part_number = len(metadata["metadata"]["parts"])
        voice_number = len([None for string in data.split("V:") if string.find("%%MIDI program ") + string.find("%%MIDI channel ") != -2])

        if part_number != voice_number:
            wrong_abc(from_path, "not the same amount of voices ({} - {})".format(voice_number, part_number))
            return

    except Exception as e:
        wrong_abc(from_path, "Error: " + e)
        return

    shutil.copy2(from_path, to_path)


# region First pass on sanitized abc

process = Process("clean_abc", "./midi/lmd_matched_flat_sanitized_abc", "./midi/lmd_matched_flat_sanitized_abc_clean")
process.step_by_function(process_function)

# endregion


# region Try to use unsanitized midi for wrong abc

process = Process("convert_wrong_abc_midi_back_to_abc_from_unsanitized", "./midi/lmd_matched_flat", "./midi/lmd_matched_flat_abc")

def path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".mid", ".abc")

job_args = []
def process_function(from_path: str, to_path: str):
    if from_path in wrong_abc_files:
        job_args.append((from_path if os.name == "posix" else from_path.replace("/", "\\"), to_path if os.name == "posix" else to_path.replace("/", "\\")))

process.step_by_function(process_function, path_converter, folder_exist_ok=True, file_exist_ok=True)


midi2abc_path = verify_software_dependency(os.path.join("abcmidi", "midi2abc.exe" if os.name == "nt" else "midi2abc"))
midi2abc_path = midi2abc_path if os.name == "posix" else midi2abc_path.replace('/', '\\')

command = midi2abc_path + " -f {} -k 0 -obpl -nogr -noly -o {}"

process.step_by_popen(command, job_args, [bytearray(), bytearray()], True, True, 10, scheduler_tick_rate=0, allocated_cores=64)

# endregion


# region Check these abc and add them if good

wrong_abc_files.clear()

process = Process("clean_abc_second_pass", "./midi/lmd_matched_flat_abc", "./midi/lmd_matched_flat_sanitized_abc_clean")
process.step_by_function(process_function, folder_exist_ok=True)

# endregion


# region Write final wrong abc

with open("./results/failed_jobs_clean_abc.json", "w") as wrong_file:
    json.dump(wrong_abc_files, wrong_file)

# endregion
