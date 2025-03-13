import os
import sys
import json
import subprocess

CORES = 6

def split_list(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

musescore_path = os.path.abspath(os.path.join("softwares", "musescore", "MuseScore4.exe" if os.name == "nt" else "musescore"))
if not os.path.exists(musescore_path):
    print("Musescore executable ({}) not found.".format(musescore_path))
    sys.exit(1)

root = "./midi/lmd_matched_genre"
if not os.path.exists(root):
    print("Source directory ({}) not found.".format(root))
    sys.exit(1)

new_root = "./midi/lmd_matched_flat_sanitized"


print("Sanitizing the dataset of midi files.")

os.makedirs(new_root)


# Creating jobs

jobs = []

for curr_root, folders, files in os.walk(root):
    for file in files:
        midi_path = os.path.join(curr_root, file)
        sanitized_midi_folder = os.path.join(new_root, curr_root.replace(root + "/", ""))
        sanitized_midi_path = os.path.join(sanitized_midi_folder, file.replace(".midi", ".mid"))

        abs_midi_path = os.path.abspath(midi_path)
        abs_sanitized_midi_path = os.path.abspath(sanitized_midi_path)

        os.makedirs(sanitized_midi_folder, exist_ok=True)
        jobs.append({
            "in": abs_midi_path if os.name == "posix" else abs_midi_path.replace("/", "\\"),
            "out": abs_sanitized_midi_path if os.name == "posix" else abs_sanitized_midi_path.replace("/", "\\")
        })


# Processing

processes = []
split_jobs = split_list(jobs, CORES)

for i, job_chunk in enumerate(split_jobs):
    jobs_json_path = os.path.abspath(f"jobs_{i}.json")
    with open(jobs_json_path, "w") as jobs_file:
        json.dump(job_chunk, jobs_file)

    if os.name == "posix":
        cmd = f"{musescore_path} -j {jobs_json_path}"
    else:
        cmd = f"{musescore_path.replace('/', '\\')} -j {jobs_json_path}"

    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append((proc, jobs_json_path))


# Wait

for proc, job_file in processes:
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print(f"Error in process for {job_file}:\n{stderr.decode()}")
    else:
        print(f"Output from {job_file}:\n{stdout.decode()}")
    os.remove(job_file)


exit(0)
# Old

wrong_files = []

if True:
    with open("./results/wrongs.json", "w") as wrong_file:
        json.dump(wrong_files, wrong_file)