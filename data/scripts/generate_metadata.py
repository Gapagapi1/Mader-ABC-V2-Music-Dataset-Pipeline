import os
import sys
import json
import time
import subprocess

CORES = 8

start_time = time.time()

musescore_path = os.path.abspath(os.path.join("softwares", "musescore", "MuseScore4.exe" if os.name == "nt" else "musescore"))
if not os.path.exists(musescore_path):
    print("Musescore executable ({}) not found.".format(musescore_path))
    sys.exit(1)

root = "./midi/lmd_matched_flat"
if not os.path.exists(root):
    print("Source directory ({}) not found.".format(root))
    sys.exit(1)

new_root = "./midi/lmd_matched_flat_metadata"


print("Generating metadata the dataset of midi files using musescore.")

print("Creating dataset folder...")
os.makedirs(new_root, exist_ok=True)


# Creating jobs
print("Creating sub-folders and registering jobs...")

jobs = []
buff = {}

for curr_root, folders, files in os.walk(root):
    for file in files:
        midi_path = os.path.join(curr_root, file)
        sanitized_midi_folder = os.path.join(new_root, curr_root.replace(root + "/", ""))
        sanitized_midi_path = os.path.join(sanitized_midi_folder, file.replace(".mid", ".json"))

        abs_midi_path = os.path.abspath(midi_path)
        abs_sanitized_midi_path = os.path.abspath(sanitized_midi_path)

        os.makedirs(sanitized_midi_folder, exist_ok=True)
        if not os.path.exists(abs_sanitized_midi_path):
            jobs.append(
                (
                    abs_midi_path if os.name == "posix" else abs_midi_path.replace("/", "\\"),
                    abs_sanitized_midi_path if os.name == "posix" else abs_sanitized_midi_path.replace("/", "\\")
                )
            )

            buff[abs_midi_path if os.name == "posix" else abs_midi_path.replace("/", "\\")] = [0, bytearray(), bytearray()]


# Processing
print("Processing...")

command = "{} {} --score-meta"

proc_count = 0

running_processes = []
job_index = 0

wrong_files = []

while job_index < len(jobs) or len(running_processes) > 0:
    while job_index < len(jobs) and len(running_processes) < CORES:
        job = jobs[job_index]
        
        if os.name == "posix":
            cmd = command.format(musescore_path, *job)
        else:
            cmd = command.format(musescore_path.replace('/', '\\'), *job)
        
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_count += 1
        running_processes.append((proc, cmd, job))
        job_index += 1

    for proc_tuple in running_processes.copy():
        proc, cmd, job = proc_tuple

        try:
            stdout, stderr = proc.communicate(timeout=0.01)
            #buff[job[0]][1] += stdout
            #buff[job[0]][2] += stderr
        except subprocess.TimeoutExpired:
            pass
       
        if proc.poll() is not None:  # process finished
            stdout, stderr = proc.communicate()
            #buff[job[0]][1] += stdout
            #buff[job[0]][2] += stderr
            #stdout, stderr = buff[job[0]][1], buff[job[0]][2]
            print("Outcome for process {}:\n\t• Command: {}\n\t• Number of fails: {}\n\t• Logs:".format(proc_count, cmd, buff[job[0]][0]))
            print("___________stderr___________\n\n{}\n____________________________".format(stderr))
            if proc.returncode != 0:
                print("\t• Error code: {}".format(proc.returncode))
                if buff[job[0]][0] > 10:
                    wrong_files.append({"in": job[0], "out": job[1]})
                    del buff[job[0]]
                else:
                    buff[job[0]][0] += 1
                    if os.name == "posix":
                        cmd_restart = command.format(musescore_path, *job)
                    else:
                        cmd_restart = command.format(musescore_path.replace('/', '\\'), *job)
                    new_proc = subprocess.Popen(cmd_restart, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    proc_count += 1
                    running_processes.append((new_proc, cmd_restart, job))
                    buff[job[0]][1] = bytearray()
                    buff[job[0]][2] = bytearray()
            else:
                print("\t• Successful!")
                with open(job[1], "wb") as json_file:
                    json_file.write(stdout)
            running_processes.remove(proc_tuple)
    print("Processing: current index = {}/{} ({:.2f}h); there are {} instances of musescore running and {} failed.".format(
        job_index,
        len(jobs),
        ((len(jobs) - job_index) * ((time.time() - start_time) / job_index)) / 3600.0,
        len(running_processes),
        len(wrong_files)
    ))
    time.sleep(0.1)

with open("./results/wrongs.json", "w") as wrong_file:
    json.dump(wrong_files, wrong_file)

exit(0)
