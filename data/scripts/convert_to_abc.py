import os
import sys
import json
import time
import subprocess

CORES = 84

start_time = time.time()

midi2abc_path = os.path.abspath(os.path.join("softwares", "abcmidi", "midi2abc.exe" if os.name == "nt" else "midi2abc"))
if not os.path.exists(midi2abc_path):
    print("midi2abc executable ({}) not found.".format(midi2abc_path))
    sys.exit(1)

root = "./midi/lmd_matched_flat_sanitized"
if not os.path.exists(root):
    print("Source directory ({}) not found.".format(root))
    sys.exit(1)

abc_root = "./midi/lmd_matched_flat_sanitized_abc"


print("Converting the dataset to abc notation.")

print("Creating dataset folder...")
os.makedirs(abc_root)


# Creating jobs
print("Creating sub-folders and registering jobs...")

jobs = []
fails = {}

for parent, folders, files in os.walk(root):
    for file in files:
        midi_path = os.path.join(parent, file)
        abc_folder = os.path.join(abc_root, parent.replace(root + "/", ""))
        abc_path = os.path.join(abc_folder, file.replace(".midi", ".abc").replace(".mid", ".abc"))

        abs_midi_path = os.path.abspath(midi_path)
        abs_abc_path = os.path.abspath(abc_path)

        os.makedirs(abc_folder, exist_ok=True)
        jobs.append(
            (
                abs_midi_path if os.name == "posix" else abs_midi_path.replace("/", "\\"),
                abs_abc_path if os.name == "posix" else abs_abc_path.replace("/", "\\")
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
        
        # -K:C | one bar per line | no group | no lyrics (old: -aul 1 L:1/1)
        if os.name == "posix":
            cmd = "{} -f {} -k 0 -obpl -nogr -noly -o {}".format(midi2abc_path, *job)
        else:
            cmd = "{} -f {} -k 0 -obpl -nogr -noly -o {}".format(midi2abc_path.replace('/', '\\'), *job)
        
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        running_processes.append((proc, cmd, job))
        job_index += 1

    for proc_tuple in running_processes.copy():
        proc, cmd, job = proc_tuple
        if proc.poll() is not None:  # process finished
            stdout, stderr = proc.communicate()
            print("Log for process {}:\n\t• command: {}\n\t• stdout (discarded)\n\t• stderr (discarded)".format(job, cmd))
            if proc.returncode != 0:
                print("\t• Error code: {}".format(proc.returncode))
                if fails[job[0]] > 10:
                    wrong_files.append({"in": job[0], "out": job[1]})
                else:
                    fails[job[0]] += 1
                    if os.name == "posix":
                        cmd_restart = "{} -f {} -k 0 -obpl -nogr -noly -o {}".format(midi2abc_path, midi_path, abc_path)
                    else:
                        cmd_restart = "{} -f {} -k 0 -obpl -nogr -noly -o {}".format(midi2abc_path.replace('/', '\\'), midi_path, abc_path)
                    new_proc = subprocess.Popen(cmd_restart, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    running_processes.append((new_proc, cmd_restart, job))
            else:
                print("\t• Successful!")
            running_processes.remove(proc_tuple)
    print("Processing: current index = {}/{} ({:.2f}h); there are {} instances of midi2abc running and {} failed.".format(
        job_index,
        len(jobs),
        ((len(jobs) - job_index) * ((time.time() - start_time) / job_index)) / 3600.0,
        len(running_processes),
        len(wrong_files)
    ))
    time.sleep(0.1)

if True:
    with open("./results/wrongs_abc.json", "w") as wrong_file:
        json.dump(wrong_files, wrong_file)

exit(0)