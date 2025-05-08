import os
import sys
import json
import shutil
import music21

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process, verify_software_dependency


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
        return (False, from_path, "no M declaration")
    elif "-" == data[M_declaration + 3]:
        return (False, from_path, "M declaration is negative")

    K_declaration = data.find("K:C ")

    if K_declaration == -1:
        return (False, from_path, "K declaration is not C")

    try:
        abc = music21.abcFormat.ABCHandler()
        abc.process(data)

        if not abc.definesMeasures():
            return (False, from_path, "not measures defined")

        if not abc.hasNotes():
            return (False, from_path, "has no notes")

        metadata_path = get_metadata_from_midi_path(from_path)

        if metadata_path == None:
            return (False, from_path, "could not create associated metadata path")

        if not os.path.exists(metadata_path):
            return (False, from_path, "metadata path does not exist")

        with open(metadata_path, "r", encoding="utf8") as metadata_file:
            metadata = json.load(metadata_file)

        part_number = len(metadata["metadata"]["parts"])
        voice_number = len([None for string in data.split("V:") if string.find("%%MIDI program ") + string.find("%%MIDI channel ") != -2])

        if part_number != voice_number:
            return (False, from_path, "not the same amount of voices ({} - {})".format(voice_number, part_number))

    except Exception as e:
        import traceback
        return (False, from_path, "Error \"{}\" : ".format(e) + traceback.format_exc())

    shutil.copy2(from_path, to_path)

    return (True, from_path, "OK")


if __name__ == "__main__":
    wrong_abc_files = {}

    def wrong_abc(from_path: str, reason: str):
        wrong_abc_files.update({from_path: reason})
        print("[clean_abc]", from_path, "is a wrong abc file:", reason)

# region First pass on sanitized abc

    process = Process("clean_abc", "./midi/lmd_matched_flat_sanitized_abc", "./midi/lmd_matched_flat_sanitized_abc_clean")
    results = process.step_by_function(process_function, useProcessExecutor=True)

    for res in results:
        is_success, from_path, reason = res
        if not is_success:
            wrong_abc(from_path, reason)

# endregion


# region Try to use unsanitized midi for wrong abc

    def path_converter(from_path: str, is_folder: bool):
        return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".mid", ".abc")

    job_args = []

    def process_function2(from_path: str, to_path: str):
        path = to_path.replace("lmd_matched_flat_abc", "lmd_matched_flat_sanitized_abc")
        if path in wrong_abc_files:
            job_args.append((from_path if os.name == "posix" else from_path.replace("/", "\\"), to_path if os.name == "posix" else to_path.replace("/", "\\")))
            del wrong_abc_files[path]

    process = Process("convert_wrong_abc_midi_back_to_abc_from_unsanitized", "./midi/lmd_matched_flat", "./midi/lmd_matched_flat_abc")
    process.step_by_function(process_function2, path_converter, folder_exist_ok=True, file_exist_ok=True)

    midi2abc_path = verify_software_dependency(os.path.join("abcmidi", "midi2abc.exe" if os.name == "nt" else "midi2abc"))
    midi2abc_path = midi2abc_path if os.name == "posix" else midi2abc_path.replace('/', '\\')

    command = midi2abc_path + " -f {} -k 0 -obpl -nogr -noly -o {}"

    process.step_by_popen(command, job_args, [bytearray(), bytearray()], True, True, 10, scheduler_tick_rate=0, allocated_cores=64)

# endregion


# region Check these abc and add them if good

    process = Process("clean_abc_second_pass", "./midi/lmd_matched_flat_abc", "./midi/lmd_matched_flat_sanitized_abc_clean", to_folder_exist_ok=True)
    results = process.step_by_function(process_function, folder_exist_ok=True, useProcessExecutor=True)

    for res in results:
        is_success, from_path, reason = res
        if not is_success:
            wrong_abc(from_path, reason)

# endregion


# region Write final wrong abc

    with open("./results/failed_jobs_clean_abc.json", "w") as wrong_file:
        json.dump(wrong_abc_files, wrong_file)

# endregion
