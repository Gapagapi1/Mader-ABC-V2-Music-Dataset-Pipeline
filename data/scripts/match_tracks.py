from os import listdir, mkdir, path
from shutil import rmtree, copy2

files_genre =  ["msd_tagtraum_cd1", "msd_tagtraum_cd2", "msd_tagtraum_cd2c", "msd-MAGD-genreAssignment", "msd-MASD-styleAssignment", "msd-topMAGD-genreAssignment"]

def get_all_matched_tracks(files_paths: list[str]):
    """
    Create a file with all the metadata tracks summarized.

    Args:
        files_paths (list[str]): List of all the metadata file paths.

    Returns:
        all_tracks (set): Set containing all tracks names.
    """
    all_tracks = {}
    for file_path in files_paths:
        single_file_tracks = get_single_matched_track("genre/" + file_path + ".cls")
        for key in single_file_tracks.keys():
            if key not in all_tracks:
                all_tracks[key] = set()
            all_tracks[key] |= single_file_tracks[key]
        
    return all_tracks

def get_single_matched_track(file_path: str):
    """
    Create a file with the specified dataset's metadata tracks summarized.

    Args:
        file_path (str): Path to the metadata file.

    Returns:
        single_track (set): Set containing all tracks names of the dataset.
    """
    single_track = {}
    file = open(file_path, "r")
    for line in file:
        splitted_line = line.split('\t')
        track_id = splitted_line[0]
        if track_id not in single_track:
            single_track[track_id] = set()
        for k in range(1, len(splitted_line)):
            single_track[track_id].add(splitted_line[k].strip())
        
    return single_track

def squash_tracks_ids():
    """
    Summurize all the (genre) metadata in one file.

    This function create all_tracks.txt
    """
    print("Start retreiving all tracks and their genre from the different databases.")
    tracks = get_all_matched_tracks(files_genre)
    tracks_str = ""
    for key in tracks.keys():
        tracks_str += key + " " + " ".join(tracks[key]) + "\n"
    with open("results/all_tracks.txt", "w") as f:
        f.write(tracks_str)
    print("Finished task")

def single_file_tracks_ids():
    """
    Summurize all the (genre) metadata in a file for each dataset.

    This function create msd_tagtraum_cd1.txt, msd_tagtraum_cd2c.txt, msd-MAGD-genreAssignment.txt, msd-MASD-styleAssignment.txt and msd-topMAGD-genreAssignment.txt 
    """
    for file in files_genre:
        tracks = get_single_matched_track("genre/" + file + ".cls")
        tracks_str = ""
        all_genres = {}
        for key in tracks.keys():
            tracks_str += key + " " + " ".join(tracks[key]) + "\n"
            for genre in tracks[key]:
                if genre not in all_genres:
                    all_genres[genre] = 0
                all_genres[genre] += 1
        with open("results/" + file + ".txt", "w") as f:
            f.write(tracks_str)
        with open("results/genres/" + file + ".txt", "w") as f:
            f.write('\n'.join(items[0] + " " + str(items[1]) for items in sorted(all_genres.items(), key=lambda x: x[1], reverse=True)))

def check_lmd_tracks():
    """
    Summurize all the tracks contained in the lmd_matched dataset.

    This function create lmd_tracks.txt
    """
    print("Start retreiving all tracks from the lmd database.")
    all_tracks = set() 
    for track in listdir("midi/lmd_matched_flat"):
        all_tracks.add(track)
    with open("results/lmd_tracks.txt", "w") as f:
        f.write('\n'.join(all_tracks))
    print("Finished task")

def check_diff(metadata_file_name:str="all_tracks", source_file_name:str="lmd_tracks"):
    """
    Checks the tracks difference between two files.

    Args:
        metadata_file_name (str): Path to the summarized metadata file.
        source_file_name (str): Path to the summarized database file.

    This function create `metadata_file_name`_diff.txt
    """
    print("Start checking the intersection between the " + metadata_file_name + " and the " + source_file_name)
    metadata = open("results/" + metadata_file_name + ".txt", "r")
    lmd = open("results/" + source_file_name + ".txt", "r")
    metadata_tracks = {}
    lmd_tracks = set()

    for track in metadata:
        splitted_tracks = track.split(' ')
        genres = []
        for k in range(1, len(splitted_tracks)):
            genres.append(splitted_tracks[k].strip())
        metadata_tracks[track.split(' ')[0]] = genres
    
    for track in lmd:
        lmd_tracks.add(track[:-1])
    
    results = {(key+ " " + " ".join(metadata_tracks[key])) for key in [key for key in lmd_tracks if key in metadata_tracks.keys()]}
    
    if (not path.exists("results/diff/")):
        mkdir("results/diff/")

    with open("results/diff/" + metadata_file_name + ".txt", "w") as f:
        f.write('\n'.join(results))
    print("Finished task")

def check_diff_each_file():
    """
    Checks the tracks difference between every dataset.
    """
    for file in files_genre:
        check_diff(file)

def get_genres(file_path:str="all_tracks.txt"):
    print("Start checking the count of the different genres of " + file_path)
    file = open("results/diff/" + file_path, "r")
    all_genres = {}
    for track in file:
        splitted_tracks = track.split(' ')
        for k in range(1, len(splitted_tracks)):
            if (splitted_tracks[k].strip() not in all_genres):
                all_genres[splitted_tracks[k].strip()] = 0
            all_genres[splitted_tracks[k].strip()] += 1
    
    if (not path.exists("results/genres")):
        mkdir("results/genres")

    with open("results/genres/" + file_path, "w") as f:
        f.write('\n'.join(items[0] + " " + str(items[1]) for items in sorted(all_genres.items(), key=lambda x: x[1], reverse=True)))
    print("Finished task")

def sort_matched_tracks():
    """
    Copy all the tracks where we have genre.
    """
    print("Start coping file where we have the genre")
    matched = open("results/diff/all_tracks.txt", "r")
    matched_tracks = set()

    for track in matched:
        matched_tracks.add(track.split(" ")[0])

    if (not path.exists("midi/lmd_matched_genre")):
        mkdir("midi/lmd_matched_genre")

    for track in listdir("midi/lmd_matched_flat"):
        if track in matched_tracks:
            if (not path.exists("midi/lmd_matched_genre/" + track)):
                mkdir("midi/lmd_matched_genre/" + track)

            for file in listdir("midi/lmd_matched_flat/" + track):
                copy2("midi/lmd_matched_flat/" + track + "/" + file, "midi/lmd_matched_genre/" + track + "/" + file)
    print("Finished task")

squash_tracks_ids()
check_lmd_tracks()
check_diff()
get_genres()
sort_matched_tracks()