import os
import sys
import json
import pickle
import music21

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process


# https://en.wikipedia.org/wiki/General_MIDI
GENERAL_MIDI_PROGRAM_CATEGORIES = {
    1:  "Piano",
    3:  "Organ",
    4:  "Guitar",
    5:  "Bass",
    6:  "String",
    7:  "Vocal",
    9:  "Brass",
    10: "Reed",
    11: "Pipe",
    12: "Synth Lead",
    13: "Synth Pad",
    15: "Synth Effect",
    2:  "Pitched Percussion",
    14: "Percussive",

    8:  "Sound Effect",

    0:  "Percussion Channel",
}

GENERAL_MIDI_PROGRAM_INSTRUMENTS_MAPPING = {
    "General MIDI Percussion": 0,

    "Acoustic Grand Piano": 1,
    "Bright Acoustic Piano": 1,
    "Electric Grand Piano": 1,
    "Honky-tonk Piano": 1,
    "Electric Piano 1": 1,
    "Electric Piano 2": 1,
    "Harpsichord": 1,
    "Clavinet": 1,

    "Celesta": 2,
    "Glockenspiel": 2,
    "Music Box": 2,
    "Vibraphone": 2,
    "Marimba": 2,
    "Xylophone": 2,
    "Tubular Bells": 2,
    "Dulcimer": 2,

    "Drawbar Organ": 3,
    "Percussive Organ": 3,
    "Rock Organ": 3,
    "Church Organ": 3,
    "Reed Organ": 3,
    "Accordion": 3,
    "Harmonica": 3,
    "Bandoneon": 3,

    "Acoustic Guitar (nylon)": 4,
    "Acoustic Guitar (steel)": 4,
    "Electric Guitar (jazz)": 4,
    "Electric Guitar (clean)": 4,
    "Electric Guitar (muted)": 4,
    "Electric Guitar (overdrive)": 4,
    "Electric Guitar (distortion)": 4,
    "Electric Guitar (harmonics)": 4,

    "Acoustic Bass": 5,
    "Electric Bass (finger)": 5,
    "Electric Bass (picked)": 5,
    "Electric Bass (fretless)": 5,
    "Slap Bass 1": 5,
    "Slap Bass 2": 5,
    "Synth Bass 1": 5,
    "Synth Bass 2": 5,

    "Violin": 6,
    "Viola": 6,
    "Cello": 6,
    "Contrabass": 6,
    "Tremolo Strings": 6,
    "Pizzicato Strings": 6,
    "Orchestral Harp": 6,
    "Timpani": 2,

    "String Ensemble 1": 6,
    "String Ensemble 2": 6,
    "Synth Strings 1": 6,
    "Synth Strings 2": 6,
    "Choir Aahs": 7,
    "Voice Oohs": 7,
    "Synth Voice": 7,
    "Orchestra Hit": 8,

    "Trumpet": 9,
    "Trombone": 9,
    "Tuba": 9,
    "Muted Trumpet": 9,
    "French Horn": 9,
    "Brass Section": 9,
    "Synth Brass 1": 9,
    "Synth Brass 2": 9,

    "Soprano Sax": 10,
    "Alto Sax": 10,
    "Tenor Sax": 10,
    "Baritone Sax": 10,
    "Oboe": 10,
    "English Horn": 10,
    "Bassoon": 10,
    "Clarinet": 10,

    "Piccolo": 11,
    "Flute": 11,
    "Recorder": 11,
    "Pan Flute": 11,
    "Blown Bottle": 11,
    "Shakuhachi": 11,
    "Whistle": 11,
    "Ocarina": 11,

    "Lead 1 (square)": 12,
    "Lead 2 (sawtooth)": 12,
    "Lead 3 (calliope)": 12,
    "Lead 4 (chiff)": 12,
    "Lead 5 (charang)": 12,
    "Lead 6 (voice)": 12,
    "Lead 7 (fifths)": 12,
    "Lead 8 (bass + lead)": 12,

    "Pad 1 (new age)": 13,
    "Pad 2 (warm)": 13,
    "Pad 3 (polysynth)": 13,
    "Pad 4 (choir)": 13,
    "Pad 5 (bowed glass)": 13,
    "Pad 6 (metallic)": 13,
    "Pad 7 (halo)": 13,
    "Pad 8 (sweep)": 13,

    "FX 1 (rain)": 15,
    "FX 2 (soundtrack)": 15,
    "FX 3 (crystal)": 15,
    "FX 4 (atmosphere)": 15,
    "FX 5 (brightness)": 15,
    "FX 6 (goblins)": 15,
    "FX 7 (echoes)": 15,
    "FX 8 (sci-fi)": 15,

    "Sitar": 4,
    "Banjo": 4,
    "Shamisen": 4,
    "Koto": 4,
    "Kalimba": 2,
    "Bag pipe": 11,
    "Fiddle": 6,
    "Shanai": 10,

    "Tinkle Bell": 14,
    "Agogô": 14,
    "Steel Drums": 14,
    "Woodblock": 14,
    "Taiko Drum": 14,
    "Melodic Tom": 14,
    "Synth Drum": 14,
    "Reverse Cymbal": 14,

    "Guitar Fret Noise": 8,
    "Breath Noise": 8,
    "Seashore": 8,
    "Bird Tweet": 8,
    "Telephone Ring": 8,
    "Helicopter": 8,
    "Applause": 8,
    "Gunshot": 8,
}


def path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path) if is_folder else os.path.basename(from_path).replace(".abc", "")

def get_metadata_from_midi_path(input_path: str) -> str | None:
    parts = input_path.split(os.sep)

    if len(parts) < 3 or not parts[-1].endswith('.abc'):
        return None

    return os.sep.join(parts[:-3] + ['lmd_matched_flat_metadata', parts[-2], os.path.splitext(parts[-1])[0] + '.json'])

def get_note_tok_name(tok, strSrc = None):
    name = tok.getPitchName(strSrc = tok.src if strSrc is None else strSrc)[0]
    return name if name is not None else "z"

def voice_to_tokens(voice):
    tokens = []
    unused_tokens = set()
    for token in voice.tokens:
        if isinstance(token, music21.abcFormat.ABCBar):
            tokens.append("|")  # TODO: additional bars
        elif isinstance(token, music21.abcFormat.ABCChord):
            tokens.append("[")
            for note in token.src.replace("[", "").split("]")[0].split(" "):
                tokens.append(str(get_note_tok_name(token, note)))
            tokens.append("]")
            tokens.append(str(token.getQuarterLength(strSrc=token.src)))
        elif isinstance(token, music21.abcFormat.ABCNote):
            tokens.append(str(get_note_tok_name(token)))
            tokens.append(str(token.getQuarterLength(strSrc=token.src)))
        else:
            unused_tokens.add(str(token.src))
    return tokens, unused_tokens

def process_function(from_path: str, to_path: str):
    os.makedirs(to_path, exist_ok=True)

    unused_tokens = set()

    with open(from_path) as abc_file:
        data = abc_file.read()

    data_voice_has_instrument_change = [voice.find("%%MIDI program ") + voice.find("%%MIDI channel ") != -2 for voice in data.split("V:")[1:]]

    if not data_voice_has_instrument_change[0]:
        return (False, from_path, "no instrument change at start")

    try:
        abc = music21.abcFormat.ABCHandler()
        abc.process(data)

        metadata_path = get_metadata_from_midi_path(from_path)
        if metadata_path == None:
            return (False, from_path, "could not create associated metadata path")
        if not os.path.exists(metadata_path):
            return (False, from_path, "metadata path does not exist")
        with open(metadata_path, "r", encoding="utf8") as metadata_file:
            metadata = json.load(metadata_file)

        voice_midi_program_dict = {}
        is_there_a_voice = False

        part_index = -1
        for i, voice in enumerate(abc.splitByVoice()[1:]):
            is_there_a_voice = True

            if data_voice_has_instrument_change[i]:
                part_index += 1

            program_id = 0 if metadata["metadata"]["parts"][part_index]["hasDrumStaff"] == "true" else (metadata["metadata"]["parts"][part_index]["program"] + 1)
            program_name = list(GENERAL_MIDI_PROGRAM_INSTRUMENTS_MAPPING.keys())[program_id]
            category_id = GENERAL_MIDI_PROGRAM_INSTRUMENTS_MAPPING[program_name]
            category_name = GENERAL_MIDI_PROGRAM_CATEGORIES[category_id]

            voice_midi_program_dict[i] = {
                "program_id": program_id,
                "program_name": program_name,
                "category_id": category_id,
                "category_name": category_name,
                "musescore_info": metadata["metadata"]["parts"][part_index]
            }

            path = os.path.join(to_path, "voice_{}.pkl".format(i))
            with open(path, "wb") as token_file:
                tokens, local_unused_tokens = voice_to_tokens(voice)
                pickle.dump(tokens, token_file)
                unused_tokens.update(local_unused_tokens)

        if not is_there_a_voice:
            return (False, from_path, "no voices found")

        path = os.path.join(to_path, "metadata.json")
        with open(path, "w", encoding="utf8") as metadata_file:
            json.dump(voice_midi_program_dict, metadata_file)

    except Exception as e:
        import traceback
        return (False, from_path, "Error \"{}\" : ".format(e) + traceback.format_exc())

    return (True, from_path, unused_tokens)


if __name__ == "__main__":
    wrong_abc_files = {}
    unused_tokens = set()

    def wrong_abc(from_path: str, reason: str):
        wrong_abc_files.update({from_path: reason})
        print("[tokenize_abc]", from_path, "is a wrong abc file:", reason)

    process = Process("tokenize_abc", "./midi/lmd_matched_flat_sanitized_abc_clean", "./midi/lmd_matched_flat_sanitized_abc_clean_tokenized")
    results = process.step_by_function(process_function, path_converter=path_converter, useProcessExecutor=True)

    for res in results:
        is_success, from_path, reason_or_unused_tokens = res
        if not is_success:
            wrong_abc(from_path, reason_or_unused_tokens)
        else:
            unused_tokens.update(reason_or_unused_tokens)

    with open("./results/failed_jobs_clean_abc_tokenize.json", "w") as wrong_file:
        json.dump(wrong_abc_files, wrong_file)

    with open("./results/unused_tokens_clean_abc_tokenize.json", "w") as wrong_file:
        json.dump(list(unused_tokens), wrong_file)
