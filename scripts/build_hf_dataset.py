import json
import pickle
import re
from tqdm import tqdm
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import ClassLabel

# --- CONFIG ---
TOK_ROOT = Path("./midi/lmd_matched_flat_sanitized_abc_clean_tokenized")
ABC_ROOT = Path("./midi/lmd_matched_flat_sanitized_abc_clean_split")
GENRE_JSON = Path("./results/msd_trackid_to_genre.json")
OUT_DIR = Path("./data")
SHARD_ROWS = 500_000  # adjust based on RAM / size
WRITE_ABC = True  # set False if you only want tokens

# --- CODE ---

INSTRUMENTS = ["Piano", "Organ", "Guitar", "Bass", "String", "Vocal", "Brass", "Reed", "Pipe", "Synth Lead", "Synth Pad", "Synth Effect", "Pitched Percussion", "Percussive", "Sound Effect", "Percussion Channel"]
instrument_label = ClassLabel(names=INSTRUMENTS)
instrument_to_id = {c:i for i,c in enumerate(INSTRUMENTS)}

GENRES = ["Rock", "Pop", "Electronic", "Country", "RnB", "Jazz", "World", "Other", "Unknown"]
genre_label = ClassLabel(names=GENRES)
genre_to_id = {g:i for i,g in enumerate(GENRES)}

VOICE_RE = re.compile(r"voice_(\d+)\.pkl")
TRACK_RE = re.compile(r"track (\d+)\.abc")

def iter_dataset(root: Path, glob_str: str, compiled_regex, is_abc_text_corpus: bool = True):
    with open(GENRE_JSON, "r", encoding="utf-8") as f:
        msd_to_genre = json.load(f)
    for track_dir in sorted(root.iterdir()):
        if not track_dir.is_dir():
            continue
        track_id = track_dir.name
        genre_name = msd_to_genre.get(track_id)
        if genre_name is None or genre_name not in genre_to_id:
            genre_name = "Unknown"
        g_id = genre_to_id[genre_name]
        for arr_dir in sorted(track_dir.iterdir()):
            if not arr_dir.is_dir():
                continue
            arrangement_id = arr_dir.name
            meta_path = TOK_ROOT / track_id / arrangement_id / "metadata.json"
            if not meta_path.exists():
                print(f"WARNING: meta_path '{meta_path}' does not exist.")
                continue
            with open(meta_path, "r", encoding="utf-8") as mf:
                voice_meta = json.load(mf)

            for path in sorted(arr_dir.glob(glob_str)):
                m = compiled_regex.search(path.name)
                if not m:
                    print(f"WARNING: {path} does not exist.")
                    continue
                voice_idx = int(m.group(1))
                try:
                    if is_abc_text_corpus:
                        content = path.read_text(encoding="utf-8")
                    else:
                        with open(path, "rb") as f:
                             content = [str(t) for t in pickle.load(f)]
                except Exception:
                    print(f"WARNING: Could not read '{path}'.")
                    continue

                vm = voice_meta.get(str(voice_idx))
                if vm is None:
                    print(f"WARNING: Found invalid voice metadata ({voice_meta}).")
                    continue

                vi = vm.get("category_name")
                if vi is None:
                    print(f"WARNING: Found invalid voice instrument ({vm}).")
                    continue

                yield {
                    "track_id": track_id,
                    "arrangement_id": arrangement_id,
                    "voice_index": voice_idx,
                    "program_id": int(vm["program_id"]),
                    "program_name": vm["program_name"],
                    "musescore_info": vm["musescore_info"],
                    "instrument_category": instrument_to_id[vi],
                    "genre_category": g_id,
                    "abc_text" if is_abc_text_corpus else "token_sequence": content,
                }

def write_parquet_shards(rows_iter, out_path):
    out_path.mkdir(parents=True, exist_ok=True)
    batch = []
    part_idx = 0
    for idx, row in tqdm(enumerate(rows_iter, 1)):
        batch.append(row)
        if len(batch) >= SHARD_ROWS:
            table = pa.Table.from_pylist(batch, schema=None)
            pq.write_table(table, out_path / f"part-{part_idx:04d}.parquet", compression="zstd")
            batch.clear()
            part_idx += 1
    if batch:
        table = pa.Table.from_pylist(batch, schema=None)
        pq.write_table(table, out_path / f"part-{part_idx:04d}.parquet", compression="zstd")

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Writing tokens parquet files...")
    write_parquet_shards(iter_dataset(TOK_ROOT, "voice_*.pkl", VOICE_RE, False), OUT_DIR / "abc_tokens")
    if WRITE_ABC:
        print("Writing abc voice parquet files...")
        write_parquet_shards(iter_dataset(ABC_ROOT, "track *.abc", TRACK_RE, True), OUT_DIR / "abc_texts")
    print("Done. Parquet shards in ./data/")

