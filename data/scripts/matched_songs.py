from os import listdir, mkdir
from shutil import rmtree

def get_all_matched_tracks(files_paths):
    for file_path in files_paths:
        all_tracks = set()
        file = open(file_path, "r")
        for line in file:
            all_tracks.add(line.split('\t')[0])
        
    return '\n'.join(all_tracks)

def get_single_matched_track(file_path):
    single_track = set()
    file = open(file_path, "r")
    for line in file:
        single_track.add(line.split('\t')[0])
        
    return '\n'.join(single_track)

def squash_tracks_ids():
    files_paths =  ["msd_tagtraum_cd1.cls", "msd_tagtraum_cd2c.cls", "msd-MAGD-genreAssignment.cls", "msd-MASD-styleAssignment.cls", "msd-topMAGD-genreAssignment.cls"]
    with open("all_tracks.txt", "w") as f:
        f.write(get_all_matched_tracks(files_paths))

def single_file_tracks_ids():
    files =  ["msd_tagtraum_cd1", "msd_tagtraum_cd2c", "msd-MAGD-genreAssignment", "msd-MASD-styleAssignment", "msd-topMAGD-genreAssignment"]
    for file in files:
        with open(file + ".txt", "w") as f:
            f.write(get_single_matched_track(file + ".cls"))

def check_lmd_tracks():
    all_tracks = set() 
    for track in listdir("lmd_matched_flatten"):
        all_tracks.add(track)
    with open("lmd_tracks.txt", "w") as f:
        f.write('\n'.join(all_tracks))

def check_diff(all_tracks_file_path):
    metadata = open("all_tracks.txt", "r")
    lmd = open("lmd_tracks.txt", "r")
    metadata_tracks = set()
    lmd_tracks = set()

    for track in metadata:
        metadata_tracks.add(track)
    
    for track in lmd:
        lmd_tracks.add(track)
    
    with open("diff.txt", "w") as f:
        f.write(''.join(lmd_tracks.intersection(metadata_tracks)))

def check_diff_each_file():
    pass

def sort_matched_tracks():
    matched = open("all_tracks.txt", "r")
    matched_tracks = set()

    for track in matched:
        matched_tracks.add(track)
    
    print(matched_tracks)

    for track in listdir("lmd_matched_flat"):
        if track not in matched_tracks:
            print(track)
            rmtree("lmd_matched_flat/" + track)
        

single_file_tracks_ids()