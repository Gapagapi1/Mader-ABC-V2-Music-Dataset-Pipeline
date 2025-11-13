import os
import json
from shutil import copy2

genre_mapping_dict = {
    "Pop_Rock": [
        "Pop",
        "Rock"
    ],
    "Rock": [
        "Rock"
    ],
    "Pop": [
        "Pop"
    ],
    "Electronic": [
        "Electronic"
    ],
    "Country": [
        "Country"
    ],
    "Pop_Contemporary": [
        "Pop"
    ],
    "RnB": [
        "RnB"
    ],
    "Rock_Contemporary": [
        "Rock"
    ],
    "Latin": [
        "World"
    ],
    "Jazz": [
        "Jazz"
    ],
    "Country_Traditional": [
        "Country"
    ],
    "Dance": [
        "Electronic"
    ],
    "Rock_Hard": [
        "Rock"
    ],
    "Metal": [
        "Rock"
    ],
    "Pop_Indie": [
        "Pop"
    ],
    "Metal_Alternative": [
        "Rock"
    ],
    "Rap": [
        "RnB"
    ],
    "International": [
        "World"
    ],
    "Rock_College": [
        "Rock"
    ],
    "Folk": [
        "Country"
    ],
    "Pop_Latin": [
        "Pop"
    ],
    "Rock_Alternative": [
        "Rock"
    ],
    "Experimental": [
        "Electronic"
    ],
    "Hip_Hop_Rap": [
        "RnB"
    ],
    "Religious": [
        "Other"
    ],
    "New_Age": [
        "Other"
    ],
    "Vocal": [
        "Jazz"
    ],
    "Blues": [
        "Jazz"
    ],
    "Folk_International": [
        "Country"
    ],
    "RnB_Soul": [
        "RnB"
    ],
    "Rock_Neo_Psychedelia": [
        "Rock"
    ],
    "Reggae": [
        "World"
    ],
    "Electronica": [
        "Electronic"
    ],
    "Gospel": [
        "Other"
    ],
    "Easy_Listening": [
        "Other"
    ],
    "Grunge_Emo": [
        "Rock"
    ],
    "Metal_Heavy": [
        "Rock"
    ],
    "Metal_Death": [
        "Rock"
    ],
    "World": [
        "World"
    ],
    "Jazz_Classic": [
        "Jazz"
    ],
    "Punk": [
        "Rock"
    ],
    "Big_Band": [
        "Jazz"
    ],
    "Blues_Contemporary": [
        "Jazz"
    ],
    "Classical": [
        "Other"
    ],
    "Stage": [
        "Other"
    ],
    "Children": [
        "Other"
    ],
    "Comedy_Spoken": [
        "Other"
    ],
    "Holiday": [
        "Other"
    ],
    "Avant_Garde": [
        "Other"
    ]
}

def get_files_names(genre_path: str):
    metadata_files = []
    for file in sorted(os.listdir(genre_path)):
        metadata_files.append(file[:-4])

    return metadata_files

def get_lmd_tracks(save_file:str = "lmd_tracks"):
    """
    Summurize all the tracks contained in the lmd_matched dataset.

    This function create lmd_tracks
    """
    print("Start retrieving all tracks from the LMD database.")
    all_tracks = set()
    for track in os.listdir("./midi/lmd_matched_flat"):
        all_tracks.add(track)
    print("Writing track list to '" + save_file + "'.")

    if (not os.path.exists("./results/tracks/")):
        os.mkdir("./results/tracks/")

    with open("./results/tracks/" + save_file, "w") as f:
        f.write('\n'.join(sorted(all_tracks)))
    print("Finished task.")

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

    print("Start retrieving all tracks and their genres from " + file_name + ".")
    tracks = {}
    tracks_str = ""

    file = open("./genre/" + file_name, "r")
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

    for key in sorted(tracks.keys()):
        tracks_str += key + " " + " ".join(sorted(tracks[key])) + "\n"
    with open("./results/tracks/" + output_name, "w") as f:
        f.write(tracks_str)

    file.close()

    return tracks

def get_all_metadata_files_mapping(files_paths: list[str], save_file:str = "all_tracks"):
    """
    Create a file with all the metadata tracks summarized.

    Args:
        files_paths (list[str]): List of all the metadata file paths.

    Returns:
        all_tracks (set): Set containing all tracks names.
    """
    print("Start retrieving all tracks and their genres from all datasets.")
    all_tracks = {}
    all_tracks_str = ""

    for file_path in sorted(files_paths):
        single_file_tracks = get_metadata_file_mapping(file_path + ".cls", file_path)
        for key in sorted(single_file_tracks.keys()):
            if key not in all_tracks:
                all_tracks[key] = []
            all_tracks[key] += single_file_tracks[key]

    for key in sorted(all_tracks.keys()):
        all_tracks_str += key + " " + " ".join(sorted(all_tracks[key])) + "\n"
    with open("./results/tracks/" + save_file, "w") as f:
        f.write(all_tracks_str)

    print("Finished task.")
    return all_tracks

def check_diff(file_name:str, source_file_name:str="lmd_tracks"):
    """
    Checks the tracks difference between two files.

    Args:
        metadata_file_name (str): Path to the summarized metadata file.
        source_file_name (str): Path to the summarized database file.

    This function create `metadata_file_name`_diff
    """
    print("Start checking the intersection between " + file_name + " and " + source_file_name + ".")
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
        f.write('\n'.join(sorted(results)))
    print("Finished task.")
    
    metadata.close()
    lmd.close()

def check_all_diffs(all_files:list[str]):
    """
    Checks the tracks difference between every dataset.
    """
    for file_name in sorted(all_files):
        get_metadata_file_mapping(file_name + ".cls")
        check_diff(file_name)
    get_all_metadata_files_mapping(all_files)
    check_diff("all_tracks")

def get_metadata_file_genres(file_name: str, output_name: str = None, do_set_mapping: bool = True):
    """
    Summurize all the (genre) metadata in a file for each dataset.

    This function create msd_tagtraum_cd1, msd_tagtraum_cd2c, msd-MAGD-genreAssignment, msd-MASD-styleAssignment and msd-topMAGD-genreAssignment 
    """
    print("Start counting the different genres in " + file_name + ".")
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
    
    tracks.close()

def get_all_metadata_files_genres(all_files:list[str]):
    """
    Checks the tracks difference between every dataset.
    """
    for file_name in sorted(all_files):
        get_metadata_file_genres(file_name)
    get_all_metadata_files_mapping(all_files)
    get_metadata_file_genres("all_tracks", do_set_mapping=False)

def sort_matched_tracks():
    """
    Copy all the tracks where we have genre.
    """
    print("Start copying files which have a known genre.")
    matched = open("./results/diff/all_tracks", "r")
    matched_tracks = set()

    for track in matched:
        matched_tracks.add(track.split(" ")[0])

    if (not os.path.exists("./midi/lmd_matched_genre")):
        os.mkdir("./midi/lmd_matched_genre")

    for track in sorted(os.listdir("./midi/lmd_matched_flat")):
        if track in sorted(matched_tracks):
            if (not os.path.exists("./midi/lmd_matched_genre/" + track)):
                os.mkdir("./midi/lmd_matched_genre/" + track)

            for file in sorted(os.listdir("./midi/lmd_matched_flat/" + track)):
                copy2("./midi/lmd_matched_flat/" + track + "/" + file, "./midi/lmd_matched_genre/" + track + "/" + file)
    print("Finished task.")
    
    matched.close()

def set_definitive_genre(genre_mapping_dict: dict):
    tracks = open("./results/diff/all_tracks", "r")

    mapping_json = genre_mapping_dict

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

        track_mapping[title] = sorted(
            track_genres.items(),
            key=lambda kv: (-kv[1], kv[0])  # higher count first, then lexicographically
        )[0][0]
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
    print("Here is the final mapping counts:", count_mapping)
    
    tracks.close()


if __name__ == "__main__":
    metadata_files = get_files_names("./genre")
    get_lmd_tracks()
    get_all_metadata_files_genres(metadata_files)
    # sort_matched_tracks()

    set_definitive_genre(genre_mapping_dict)
    
    with open("./results/mapping/all_tracks", "r") as file:
        json_content = "{\n" + "".join(["\t\"" + line.split(" ")[0] + "\"" + ": " + "\"" + line.split(" ")[1].replace("\n", "") + "\",\n" for line in file.readlines()])[:-1] + "\n}"
    with open("./results/msd_trackid_to_genre.json", "w") as file:
        file.write(json_content)