import os
import json
from shutil import rmtree, copy2

os.chdir('./data')

def get_files_names(genre_path: str):
    metadata_files = []
    for file in os.listdir(genre_path):
        metadata_files.append(file[:-4])

    return metadata_files

def get_lmd_tracks(save_file:str = "lmd_tracks"):
    """
    Summurize all the tracks contained in the lmd_matched dataset.

    This function create lmd_tracks
    """
    print("Start retreiving all tracks from the lmd database.")
    all_tracks = set()
    for track in os.listdir("./midi/lmd_matched_flat"):
        all_tracks.add(track)
    print("Outputing into '" + save_file + "'.")

    if (not os.path.exists("./results/tracks/")):
        os.mkdir("./results/tracks/")

    with open("./results/tracks/" + save_file, "w") as f:
        f.write('\n'.join(all_tracks))
    print("Finished task")

def get_metadata_file_mapping(file_name: str, output_name: str = None):
    """
    Create a file with the specified dataset's metadata tracks summarized.

    Args:
        file_path (str): Name of the metadata file.

    Returns:
        single_track (dict): Set containing all tracks names of the dataset, associted to their genres.
    """
    if (output_name == None):
        output_name = file_name[:-4]

    print("Start retreiving all tracks and their genre from " + file_name + ".")
    tracks = {}
    tracks_str = ""

    file = open("./genre/metadata_files/" + file_name, "r")
    for line in file:
        if line[0] == '#':
            continue
        splitted_line = line.split('\t')
        track_id = splitted_line[0]
        if track_id not in tracks:
            tracks[track_id] = set()
        for k in range(1, len(splitted_line)):
            if (splitted_line[k].strip() == "New Age"):
                splitted_line[k] = "New_Age"

            tracks[track_id].add(splitted_line[k].strip())

    for key in tracks.keys():
        tracks_str += key + " " + " ".join(tracks[key]) + "\n"
    with open("./results/tracks/" + output_name, "w") as f:
        f.write(tracks_str)

    return tracks


def get_all_metadata_files_mapping(files_paths: list[str], save_file:str = "all_tracks"):
    """
    Create a file with all the metadata tracks summarized.

    Args:
        files_paths (list[str]): List of all the metadata file paths.

    Returns:
        all_tracks (set): Set containing all tracks names.
    """
    print("Start retreiving all tracks and their genre from the different databases.")
    all_tracks = {}
    all_tracks_str = ""

    for file_path in files_paths:
        single_file_tracks = get_metadata_file_mapping(file_path + ".cls", file_path)
        for key in single_file_tracks.keys():
            if key not in all_tracks:
                all_tracks[key] = []
            all_tracks[key] += single_file_tracks[key]

    for key in all_tracks.keys():
        all_tracks_str += key + " " + " ".join(all_tracks[key]) + "\n"
    with open("./results/tracks/" + save_file, "w") as f:
        f.write(all_tracks_str)

    print("Finished task")
    return all_tracks

def check_diff(file_name:str, source_file_name:str="lmd_tracks"):
    """
    Checks the tracks difference between two files.

    Args:
        metadata_file_name (str): Path to the summarized metadata file.
        source_file_name (str): Path to the summarized database file.

    This function create `metadata_file_name`_diff
    """
    print("Start checking the intersection between the " + file_name + " and the " + source_file_name)
    metadata = open("./results/tracks/" + file_name, "r")
    lmd = open("./results/tracks/" + source_file_name, "r")
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

    if (not os.path.exists("./results/diff/")):
        os.mkdir("./results/diff/")

    with open("./results/diff/" + file_name, "w") as f:
        f.write('\n'.join(results))
    print("Finished task")

def check_all_diffs(all_files:list[str]):
    """
    Checks the tracks difference between every dataset.
    """
    for file_name in all_files:
        get_metadata_file_mapping(file_name + ".cls")
        check_diff(file_name)
    get_all_metadata_files_mapping(all_files)
    check_diff("all_tracks")

def get_metadata_file_genres(file_name: str, output_name: str = None, do_set_mapping: bool = True):
    """
    Summurize all the (genre) metadata in a file for each dataset.

    This function create msd_tagtraum_cd1, msd_tagtraum_cd2c, msd-MAGD-genreAssignment, msd-MASD-styleAssignment and msd-topMAGD-genreAssignment 
    """
    print("Start checking the count of the different genres of " + file_name)
    if (output_name == None):
        output_name = file_name

    if (do_set_mapping):
        get_metadata_file_mapping(file_name + ".cls")

    check_diff(file_name)
    tracks = open("./results/tracks/" + file_name, "r")

    all_genres = {}

    for track in tracks:
        splitted_tracks = track.split(' ')
        for k in range(1, len(splitted_tracks)):
            if (splitted_tracks[k].strip() not in all_genres):
                all_genres[splitted_tracks[k].strip()] = 0
            all_genres[splitted_tracks[k].strip()] += 1

    if (not os.path.exists("./results/genres/")):
        os.mkdir("./results/genres/")

    with open("./results/genres/" + output_name, "w") as f:
        f.write('\n'.join(items[0] + " " + str(items[1]) for items in sorted(all_genres.items(), key=lambda x: x[1], reverse=True)))

def get_all_metadata_files_genres(all_files:list[str]):
    """
    Checks the tracks difference between every dataset.
    """
    for file_name in all_files:
        get_metadata_file_genres(file_name)
    get_all_metadata_files_mapping(all_files)
    get_metadata_file_genres("all_tracks", do_set_mapping=False)

def sort_matched_tracks():
    """
    Copy all the tracks where we have genre.
    """
    print("Start coping file where we have the genre")
    matched = open("./results/diff/all_tracks", "r")
    matched_tracks = set()

    for track in matched:
        matched_tracks.add(track.split(" ")[0])

    if (not os.path.exists("./midi/lmd_matched_genre")):
        os.mkdir("./midi/lmd_matched_genre")

    for track in os.listdir("./midi/lmd_matched_flat"):
        if track in matched_tracks:
            if (not os.path.exists("./midi/lmd_matched_genre/" + track)):
                os.mkdir("./midi/lmd_matched_genre/" + track)

            for file in os.listdir("./midi/lmd_matched_flat/" + track):
                copy2("./midi/lmd_matched_flat/" + track + "/" + file, "./midi/lmd_matched_genre/" + track + "/" + file)
    print("Finished task")

def set_definitive_genre(genre_mapping_path: str):
    tracks = open("./results/diff/all_tracks", "r")
    mapping_file = open(genre_mapping_path, "r")

    mapping_json = json.load(mapping_file)

    track_mapping = {}
    count_mapping = {}

    selection = ""
    for track in tracks:
        track = track.strip()
        title = track.split(' ')[0]
        genres = track.split(' ')[1:]
        track_genres = {}

        for subgenre in genres:
            for genre in mapping_json[subgenre]:
                if (genre not in track_genres):
                    track_genres[genre] = 0
                track_genres[genre] += 1

        track_mapping[title] = max(track_genres, key=track_genres.get)
        selection += title + " : " + str(track_genres) + " -> " + str(track_mapping[title]) + "\n"
        if (max(track_genres, key=track_genres.get) not in count_mapping):
            count_mapping[max(track_genres, key=track_genres.get)] = 0
        count_mapping[max(track_genres, key=track_genres.get)] += 1


    if (not os.path.exists("./results/mapping/")):
        os.mkdir("./results/mapping/")

    with open("./results/mapping/all_tracks", "w") as f:
        f.write('\n'.join(items[0] + " " + str(items[1]) for items in sorted(track_mapping.items(), key=lambda x: x[1], reverse=True)))
    with open("./results/mapping/selection", "w") as f:
        f.write(selection)
    print(count_mapping)



if __name__ == "__main__":
    metadata_files = get_files_names("./genre/metadata_files")
    get_lmd_tracks()
    get_all_metadata_files_genres(metadata_files)
    # sort_matched_tracks()

    set_definitive_genre("./genre/mapping.json")
