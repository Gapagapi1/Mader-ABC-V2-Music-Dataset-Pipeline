import datetime
import json
import os
import pickle
import music21
import re
from fractions import Fraction
from typing import Dict, List, Tuple, Any, Optional

def encode_abc_to_tokens(abc_text: str) -> Tuple[bool, Dict[str, Any]]:
    """
    - Takes ABC text
    - Returns {"voice_tokens": {idx: tokens}, "unused_tokens": [...]}
    """
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

    data = abc_text

    try:
        abc = music21.abcFormat.ABCHandler()
        abc.process(data)

        voice_tokens: Dict[int, List[str]] = {}
        unused_tokens = set()
        is_there_a_voice = False

        for i, voice in enumerate(abc.splitByVoice()):
            is_there_a_voice = True

            tokens, local_unused = voice_to_tokens(voice)
            voice_tokens[i] = tokens
            unused_tokens.update(local_unused)

        if not is_there_a_voice:
            return False, {"error": "no voices found"}

        return True, {
            "voice_tokens": voice_tokens,
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

        if isinstance(token, float) or (isinstance(token, str) and "." in str(token) and is_float):
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

        match = re.match(r"([A-Ga-g])([#n-]?)(-?\d+)", str(token))
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
    # ok, result = encode_abc_to_tokens(abc_text_string)
    # if ok:
    #     print(result)

    # 2) Token list (may contain multiple voices) -> ABC string list (one for each voice)
    # abc_strs = decode_tokens_to_abc(["C4", "1.0", "E4", "1.0", "[", "G4", "C5", "]", "2.0"], is_concat_chord=False)
    # print(abc_strs)
    pass
