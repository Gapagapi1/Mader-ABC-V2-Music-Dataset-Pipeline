import os
import sys

abc_root = "./midi/lmd_matched_flat_sanitized_abc"
if not os.path.exists(root):
    print("Source directory ({}) not found.".format(root))
    sys.exit(1)

split_abc_root = "./midi/lmd_matched_flat_sanitized_abc_split"


print("Splitting abc tracks into different files.")

print("Creating dataset folder...")
os.makedirs(abc_root)

for parent, folders, files in os.walk(abc_root):
    for file in files:
        abc_path = os.path.join(parent, file)
        split_abc_folder = os.path.join(split_abc_root, root.replace(abc_root + "/", ""))
        split_abc_path = os.path.join(split_abc_folder, file)
        
        # L:1/1 | -K:C | one bar per line | no group | no lyrics -aul 1 
        command = "midi2abc.exe -f {} -k 0 -obpl -nogr -noly -o {}".format(midi_path, abc_path)

        os.makedirs(abc_folder, exist_ok=True)
        
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            wrong_files.append(midi_path)
            print(f"Error executing command on {midi_path}: {e}")