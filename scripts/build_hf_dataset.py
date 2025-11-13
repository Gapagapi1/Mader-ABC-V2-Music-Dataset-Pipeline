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

# 9-class mapping
GENRES = ["Rock", "Pop", "Electronic", "Country", "RnB", "Jazz", "World", "Other", "Unknown"]
genre_label = ClassLabel(names=GENRES)
genre_to_id = {g:i for i,g in enumerate(GENRES)}

VOICE_RE = re.compile(r"voice_(\d+)\.pkl")
TRACK_RE = re.compile(r"track (\d+)\.abc")

def iter_token_dataset():
    with open(GENRE_JSON, "r", encoding="utf-8") as f:
        msd_to_genre = json.load(f)
    # Walk {track_id}/{arrangement_id}/voice_*.pkl
    for track_dir in sorted(TOK_ROOT.iterdir()):
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
            meta_path = arr_dir / "metadata.json"
            if not meta_path.exists():
                print(f"WARNING: meta_path '{meta_path}' does not exist.")
                continue
            with open(meta_path, "r", encoding="utf-8") as mf:
                voice_meta = json.load(mf)

            for pkl_path in sorted(arr_dir.glob("voice_*.pkl")):
                m = VOICE_RE.search(pkl_path.name)
                if not m:
                    print(f"WARNING: {pkl_path} is not a valid voice pickle name.")
                    continue
                voice_idx = int(m.group(1))
                try:
                    with open(pkl_path, "rb") as f:
                        tokens = pickle.load(f)
                except Exception:
                    print(f"WARNING: Could not open '{pkl_path}'.")
                    continue

                vm = voice_meta.get(str(voice_idx))
                if vm is None:
                    print(f"WARNING: Found invalid voice metadata ({voice_meta}).")
                    continue

                yield {
                    "track_id": track_id,
                    "arrangement_id": arrangement_id,
                    "voice_index": voice_idx,
                    "program_id": int(vm["program_id"]),
                    "program_name": vm["program_name"],
                    "category_id": int(vm["category_id"]),
                    "category_name": vm["category_name"],
                    "musescore_info": vm["musescore_info"],
                    "genre": g_id,
                    "tokens": [str(t) for t in tokens],
                }

def iter_abc_dataset():
    with open(GENRE_JSON, "r", encoding="utf-8") as f:
        msd_to_genre = json.load(f)
    # Walk {track_id}/{arrangement_id}/track N.abc
    for track_dir in sorted(ABC_ROOT.iterdir()):
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
            for abc_path in sorted(arr_dir.glob("track *.abc")):
                m = TRACK_RE.search(abc_path.name)
                if not m: 
                    print(f"WARNING: abc_path '{abc_path}' does not exist.")
                    continue
                track_num = int(m.group(1))
                try:
                    abc_text = abc_path.read_text(encoding="utf-8")
                except Exception:
                    print(f"WARNING: Could not read abc file '{abc_path}'.")
                    continue
                yield {
                    "track_id": track_id,
                    "arrangement_id": arrangement_id,
                    "track_num": track_num,
                    "genre": g_id,
                    "abc": abc_text,
                }

def write_parquet_shards(rows_iter, out_path):
    out_path.mkdir(parents=True, exist_ok=True)
    batch = []
    part_idx = None
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
    print("Writing tokens parquet files...")
    write_parquet_shards(iter_token_dataset(), OUT_DIR / "tokens")
    if WRITE_ABC:
        print("Writing abc voice parquet files...")
        write_parquet_shards(iter_abc_dataset(), OUT_DIR / "abc_tracks")
    print("Done. Parquet shards in ./data/")

