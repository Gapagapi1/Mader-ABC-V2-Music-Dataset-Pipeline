import datetime
import json
import os
import pickle
import music21
import re
from fractions import Fraction
from typing import Dict, List, Tuple, Any, Optional

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


def get_note_tok_name(tok, strSrc=None):
    name = tok.getPitchName(strSrc=tok.src if strSrc is None else strSrc)[0]
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


def encode_abc_to_tokens(abc_text: str, musescore_metadata: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    - Takes ABC text and MuseScore metadata path
    - Returns {"voice_tokens": {idx: tokens}, "voice_metadata": {...}, "unused_tokens": [...]}
    """
    data = abc_text
    data_voice_has_instrument_change = [voice.find("%%MIDI program ") + voice.find("%%MIDI channel ") != -2 for voice in data.split("V:")[1:]]

    if not data_voice_has_instrument_change or not data_voice_has_instrument_change[0]:
        return False, {"error": "no instrument change at start"}

    try:
        abc = music21.abcFormat.ABCHandler()
        abc.process(data)

        metadata = musescore_metadata

        voice_tokens: Dict[int, List[str]] = {}
        voice_midi_program_dict: Dict[int, Dict[str, Any]] = {}
        unused_tokens = set()
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

            tokens, local_unused = voice_to_tokens(voice)
            voice_tokens[i] = tokens
            unused_tokens.update(local_unused)

        if not is_there_a_voice:
            return False, {"error": "no voices found"}

        return True, {
            "voice_tokens": voice_tokens,
            "voice_metadata": voice_midi_program_dict,
            "unused_tokens": sorted(unused_tokens),
        }

    except Exception as e:
        import traceback
        return False, {"error": f"Error \"{e}\" : " + traceback.format_exc()}


def decode_tokens_to_abc(tokens: List[str], is_concat_chord: bool = False, header: Optional[str] = None) -> List[str]:
    """
    - Takes a token sequence and returns an ABC string as a list of voices.
    """
    header = header if header is not None else default_abc_header

    def token_to_abc(token):
        is_float = False
        try:
            float(token)
            is_float = True
        except ValueError:
            pass

        if isinstance(token, float) or (isinstance(token, str) and '.' in str(token) and is_float):
            frac = Fraction(str(token)).limit_denominator(16)
            if frac == 1:
                return True, ''
            elif frac.denominator == 1:
                return True, str(frac.numerator)
            else:
                return True, f"{frac.numerator}/{frac.denominator}"

        if token in {'[', ']', '|', 'z'}:
            return False, token

        if is_concat_chord and len(re.findall(r'\d+', str(token))) > 1:
            return False, [token_to_abc(tok) for tok in re.findall(r'[^-\d]*-?\d+', str(token))]

        match = re.match(r"([A-Ga-g])([#b\-]?)(-?\d+)", str(token))
        if match:
            note, accidental, octave = match.groups()
            octave = int(octave)

            if octave > 4:
                note = note.lower() + "'" * (octave - 5)
            elif octave < 4:
                note = note.upper() + "," * (3 - octave)
            else:
                note = note.upper()

            if accidental == '#':
                note = '^' + note
            elif accidental == '-':
                note = '_' + note
            elif accidental == 'n':
                note = '=' + note

            return False, note

        return False, str(token)

    def append_token(song_list, is_fraction, token_str):
        if token_str == '|':
            song_list.append(' |\n')
        else:
            if not is_fraction and (len(song_list) > 0 and song_list[-1][-1] != "\n"):
                song_list.append(' ')
            if token_str != "":
                song_list.append(token_str)

    def get_song(curr_tokens:list[str], index:int):
        song_list = []
        for i, token in enumerate(curr_tokens):
            is_fraction, token_str = token_to_abc(token)
            if isinstance(token_str, list):
                append_token(song_list, is_fraction, "[")
                for ele in token_str:
                    append_token(song_list, *ele)
                append_token(song_list, is_fraction, "]")
            else:
                append_token(song_list, is_fraction, token_str)

        return header + ''.join(song_list).rstrip()

    voices = []
    curr_tokens = []
    index = 0

    for token in tokens:
        if token == '/':
            if len(curr_tokens) > 0:
                voices.append(get_song(curr_tokens, index))
                index += 1
                curr_tokens.clear()
        else:
            curr_tokens.append(token)

    if len(curr_tokens) > 0:
        voices.append(get_song(curr_tokens, index))
        index += 1
        curr_tokens.clear()

    print(f"Extracted {index} songs.")

    return voices


default_abc_header = """X: 1
M: 1/4
L: 1/8
Q:1/4=72
K:C

"""

if __name__ == "__main__":
    # EXAMPLES:
    # 1) ABC string -> Token list
    # ok, result = encode_abc_to_tokens(abc_text_string, "path/to/musescore_metadata.json")
    # if ok:
    #     print(result)

    # 2) Token list (may contain multiple voices) -> ABC string list (one for each voice)
    # abc_str = decode_tokens_to_abc(["C4", "1.0", "E4", "1.0", "[", "G4", "C5", "]", "2.0"], is_concat_chord=False)
    # print(abc_str)
    pass
