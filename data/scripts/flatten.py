import os
import shutil
import json

print("Flattening the dataset")

root = "./midi/lmd_matched"

if not os.path.exists(root):
    print("Source directory not found.")
    [][0]

new_root = "./midi/lmd_matched_flat"

os.makedirs(new_root)

tracks = []
versions = {}

for root, folders, files in os.walk(root):
    if len(files) == 0:
        # print("[NOTHING] root: {} | folders: {} | files: {}".format(root, folders, files))
        continue

    last_folder = os.path.basename(root)
    new_last_folder_path = os.path.join(new_root, last_folder)
    
    if not os.path.exists(new_last_folder_path):
        os.makedirs(new_last_folder_path)
    else:
        None
        print("[STRANGE] root: {} | folders: {} | files: {}".format(root, folders, files))

    tracks.append(root.split("/")[-1])
    
    for file in files:
        src_file = os.path.join(root, file)
        dest_file = os.path.join(new_last_folder_path, file)

        if os.path.exists(dest_file):
            None
            print("[MEGA STRANGE] root: {} | folders: {} | files: {}".format(root, folders, files))

        shutil.copy2(src_file, dest_file)

        key = root.split("/")[-1]
        value = ".".join(dest_file.split(".")[:-1]).split("/")[-1]
        
        if key in versions:
            versions[key].append(value)
        else:
            versions[key] = [value]
        # print("[COPY] root: {} | folders: {} | file: {}".format(root, folders, file))

if True:
    with open("../tracks.json", "w") as tracks_file:
        json.dump(tracks, tracks_file)
    with open("../versions.json", "w") as versions_file:
        json.dump(versions, versions_file)
