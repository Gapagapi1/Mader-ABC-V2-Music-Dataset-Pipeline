import os
import sys
import json
import time
import subprocess

CORES = 14

start_time = time.time()

musescore_path = os.path.abspath(os.path.join("softwares", "musescore", "MuseScore4.exe" if os.name == "nt" else "musescore"))
if not os.path.exists(musescore_path):
    print("Musescore executable ({}) not found.".format(musescore_path))
    sys.exit(1)

root = "./midi/lmd_matched_flat"
if not os.path.exists(root):
    print("Source directory ({}) not found.".format(root))
    sys.exit(1)

new_root = "./midi/lmd_matched_flat_sanitized"


print("Sanitizing the dataset of midi files.")

print("Creating dataset folder...")
os.makedirs(new_root)


# Creating jobs
print("Creating sub-folders and registering jobs...")

jobs = []
fails = {}

for curr_root, folders, files in os.walk(root):
    for file in files:
        midi_path = os.path.join(curr_root, file)
        sanitized_midi_folder = os.path.join(new_root, curr_root.replace(root + "/", ""))
        sanitized_midi_path = os.path.join(sanitized_midi_folder, file)

        abs_midi_path = os.path.abspath(midi_path)
        abs_sanitized_midi_path = os.path.abspath(sanitized_midi_path)

        os.makedirs(sanitized_midi_folder, exist_ok=True)
        jobs.append(
            (
                abs_midi_path if os.name == "posix" else abs_midi_path.replace("/", "\\"),
                abs_sanitized_midi_path if os.name == "posix" else abs_sanitized_midi_path.replace("/", "\\")
            )
        )

        fails[abs_midi_path if os.name == "posix" else abs_midi_path.replace("/", "\\")] = 0


# Processing
print("Processing...")

running_processes = []
job_index = 0

wrong_files = []

while job_index < len(jobs) or len(running_processes) > 0:
    while job_index < len(jobs) and len(running_processes) < CORES:
        job = jobs[job_index]
        
        if os.name == "posix":
            cmd = "{} {} -o {}".format(musescore_path, *job)
        else:
            cmd = "{} {} -o {}".format(musescore_path.replace('/', '\\'), *job)
        
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        running_processes.append((proc, cmd, job))
        job_index += 1

    for proc_tuple in running_processes.copy():
        proc, cmd, job = proc_tuple
        if proc.poll() is not None:  # process finished
            stdout, stderr = proc.communicate()
            print("Log for process {}:\n\t• command: {}\n\t• stdout: {}\n\t• stderr: {}".format(job, cmd, stdout.decode('utf-8'), stderr.decode('utf-8')))
            if proc.returncode != 0:
                print("\t• Error code: {}".format(proc.returncode))
                if fails[job[0]] > 10:
                    wrong_files.append({"in": job[0], "out": job[1]})
                else:
                    fails[job[0]] += 1
                    if os.name == "posix":
                        cmd_restart = "{} {} -o {}".format(musescore_path, *job)
                    else:
                        cmd_restart = "{} {} -o {}".format(musescore_path.replace('/', '\\'), *job)
                    new_proc = subprocess.Popen(cmd_restart, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    running_processes.append((new_proc, cmd_restart, job))
            else:
                print("\t• Successful!")
            running_processes.remove(proc_tuple)
    print("Processing: current index = {}/{} ({:.2f}h); there are {} instances of musescore running and {} failed.".format(
        job_index,
        len(jobs),
        ((len(jobs) - job_index) * ((time.time() - start_time) / job_index)) / 3600.0,
        len(running_processes),
        len(wrong_files)
    ))
    time.sleep(0.1)

if True:
    with open("./results/wrongs.json", "w") as wrong_file:
        json.dump(wrong_files, wrong_file)

exit(0)
