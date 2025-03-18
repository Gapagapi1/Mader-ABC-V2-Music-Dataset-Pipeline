import os
import sys

abc_root = "./midi/lmd_matched_flat_sanitized_abc"
if not os.path.exists(abc_root):
    print("Source directory ({}) not found.".format(abc_root))
    sys.exit(1)

split_abc_root = "./midi/lmd_matched_flat_sanitized_abc_split"

print("Splitting abc tracks into different files.")

print("Creating dataset folder...")
os.makedirs(split_abc_root)

print("Spliting and writting tracks...")
for parent, folders, files in os.walk(abc_root):
    for file in files:
        abc_path = os.path.join(parent, file)
        split_abc_folder = os.path.join(split_abc_root, parent.replace(abc_root + "/", ""))
        split_abc_path = os.path.join(split_abc_folder, file)
        split_abc_subfolder = split_abc_path.replace(".abc", "")

        os.makedirs(split_abc_subfolder, exist_ok=True)
        
        with open(abc_path, 'r') as abc_file:
            lines = abc_file.readlines()

        track = 0

        header = ""

        for line in lines:
            track_path = os.path.join(split_abc_subfolder, "track {}.abc".format(track))
            
            if line.startswith("V:"):
                track += 1
                track_path = os.path.join(split_abc_subfolder, "track {}.abc".format(track))
                with open(track_path, 'a') as split_abc_file:
                    split_abc_file.write(header)
                continue

            if track == 0:
                header += line
                continue
            
            with open(track_path, 'a') as split_abc_file:
                split_abc_file.write(line)
