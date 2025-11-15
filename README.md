# 🎵 Mader ABC V2 - Music Dataset Pipeline

This repository contains a **data pipeline** that converts raw [MIDI](https://en.wikipedia.org/wiki/MIDI) collections into a **clean, normalized, tokenized** [ABC](https://en.wikipedia.org/wiki/ABC_notation) **corpus** suitable for music classification and generation tasks. At a high level, the pipeline:

1. Installs required tools,
2. Fetches and lays out the raw data,
3. Generates metadata (instruments, parts, structure) from MIDI files,
4. Sanitizes and normalizes MIDI files,
5. Converts MIDI files to ABC files,
6. Validates/cleans ABC files,
7. Tokenizes ABC files into model-friendly sequences,
8. Splits tracks into separate files,
9. Aggregates tokens to a vocabulary file,
10. And export everything to parquet format.

The pipeline relies on well-established tooling:

* **MuseScore CLI** for robust MIDI parsing/normalization and metadata export, especially where other tools struggle with timing/quantization variants.
* **midi2abc** for MIDI to ABC conversion (with specific flags to standardize key/armature and formatting).
* **music21** for ABC validation/cleaning and feature extraction.

> Background and design choices are documented in the associated [report](./REPORT.md).


## 🧭 Project Family

This work is part of a 4-part project:

1. **Data Pipeline** → (this repo) – The dataset pipeline code.
2. **Dataset** → [🤗 Mader ABC V2 - Music Dataset](https://huggingface.co/datasets/Gapagapi1/mader-abc-v2-music-dataset) – Ready-to-use dataset.
3. **Model Code** → [GitHub: Mader ABC V2 - Music Model Architectures](https://github.com/Gapagapi1/mader-abc-v2-music-model-architectures) – Model architectures and training scripts for music classification and generation. (WIP)
4. **Trained Models** → [🤗 Mader ABC V2 - Music Models](https://huggingface.co/models?search=Gapagapi1) – Pretrained checkpoints for generation and classification models. (WIP)


## 💻 Platform & Compatibility

* The pipeline has been **tested on MINGW64 UCRT** (Git Bash / MSYS2 environment on Windows) **and on Linux** (NixOS).
* Each part of the code was **written with Unix/POSIX/Linux compatibility in mind**.


## 📋 Prerequisites

* Bash shell, `wget`, `tar` and `unzip`
* Disk space and a file system that allows for a lot of files (~4,500,000 Files, ~100 GB)
* Python 3 (tested with 3.11), with the python environment described in `pyproject.toml`
* MuseScore 4


## 🚀 Quick Start

```bash
# 0) Clone this repo, then create the Python environment (here, with `uv`)
uv sync

# 1) Then, run the pipeline in order:
./scripts/setup_softwares.sh
./scripts/setup_data.sh
uv run ./scripts/flatten.py
uv run ./scripts/match_tracks.py
uv run ./scripts/generate_metadata.py
uv run ./scripts/sanitize_midi.py
uv run ./scripts/convert_to_abc.py
uv run ./scripts/clean_abc.py
uv run ./scripts/tokenize_abc.py
uv run ./scripts/split_abc_tracks.py

# 2) Optionals
# Build the Hugging Face Parquet dataset.
uv run ./scripts/build_hf_dataset.py

# Get the vocabulary of the token dataset.
uv run ./scripts/all_tokens.py

# You can replace ./scripts/convert_to_abc.py with the following script
# if you want to convert midi to musicxml rather than abc.
# Note that the pipeline ends at this point if you choose this path.
uv run ./scripts/convert_to_musicxml.py

# Clears everything (you probably don't want that).
./scripts/clear_data.sh
```

Each script is documented in details in a following section.

Outputs will be created under project subfolders (see each script's description).

Note that some tracks may contain almost no ABC token sequence and empty metadata at the end of the pipeline (53 tracks in our run), you can remove them.


## 📁 Repository Structure

The repository and the folders created by the pipeline are organized as follows:

| Folder | Created By | Description |
|---------|-------------|-------------|
| `archives/` | Pipeline | Stores **raw downloaded archives** and other temporary artifacts retrieved by `setup_data.sh`. The script unpacks them into working directories used by later steps. |
| `data/` | Pipeline | Contains the **final Parquet-formatted dataset** produced by the pipeline. |
| `genre/` | Pipeline | Holds the **genre annotation datasets** used for track/genre matching. |
| `midi/` | Pipeline | Hierarchical structure with subfolders representing **each intermediate processing step** of the MIDI to ABC pipeline. |
| `results/` | Pipeline | Contains **outputs and intermediate results**, such as genre mappings, logs, token vocabularies and success/failure summaries. |
| `scripts/` | Repository | All **pipeline code and orchestration scripts**. This is where you'll find the step-by-step executables documented bellow. |
| `softwares/` | Pipeline | Contains **downloaded third-party tools**, binaries, and symlinks (e.g., MuseScore CLI and abcMIDI suite) configured by `setup_softwares.sh`. These are required for MIDI to ABC conversion and metadata extraction. |

> Note: As specified in the "Created By" column, some of these directories are **created automatically** when you run the pipeline for the first time. They will appear in the repository when you execute the corresponding steps.


## 🗂️ Pipeline Scripts

⚠  All scripts expect to be run from the root of the repo.

### 1) `./scripts/setup_softwares.sh`

Bootstrap all third-party tools used by the pipeline: the **abcMIDI** suite (for `midi2abc`) and a path for the **MuseScore CLI**.

⚠  **You must edit before running**

1. Open the script and:

   * Uncomment **exactly one** of the function calls at the bottom (`setup_softwares_linux` **or** `setup_softwares_windows`).
   * Fix the **MuseScore path**:

     * Linux: replace `'/path/to/musescore/binary/parent/directory'` with the real directory containing the MuseScore CLI binary (e.g., `/usr/bin` or `/nix/store/...`).
     * Windows: confirm the `mklink` command points to something like `C:\Program Files\MuseScore 4\bin`.

   * Remove the `exit 1` (by design until you edit paths and uncomment the correct setup function).

2. Optionally comment the final `git restore setup_softwares.sh` (otherwise your edits will be reverted, which is handy once you've learned the exact steps).

> In the event that links to the abcMIDI suite do not work anymore, I have made sure that they are all saved in the [Internet Archive Wayback Machine](https://web.archive.org/).


### 2) `./scripts/setup_data.sh`

Fetch and organize all **source datasets and annotations** used by the pipeline. It downloads archives and plain files, extracts what's needed, and lays out a predictable directory structure so later steps can find MIDI files and genre labels. The script is **idempotent**: it skips downloads/extractions that already exist.

> In the event that links to the datasets do not work anymore, I have made sure that they are all saved in the [Internet Archive Wayback Machine](https://web.archive.org/).


### 3) `./scripts/flatten.py`

Copy all MIDI files from their original nested structure into a flat, consistent directory layout.


### 4) `./scripts/match_tracks.py`

Consolidate and reconcile genre annotations from multiple MSD/Tagtraum metadata sources with the LMD-matched MIDI tracks, compute consistent genre assignments for each piece, and output a unified, cleaned, and deterministic genre mapping for the dataset in `./results/msd_trackid_to_genre.json`.


### 5) `./scripts/generate_metadata.py`

Extract instrument and structural metadata from each MIDI file by invoking MuseScore in batch with a custom scheduler. It produces one JSON metadata file per song or arrangement for downstream alignment and analysis.


### 6) `./scripts/sanitize_midi.py`

Re-export and normalize MIDI files through MuseScore (using the custom scheduler) to sanitize their content (ensure consistent timing, encoding, and format compliance). This enables midi2abc to focus on converting rather than MIDI standardization.


### 7) `./scripts/convert_to_abc.py`

Convert sanitized MIDI files to standardized ABC notation using midi2abc with fixed key and formatting options to harmonize the musical structure and prepare data for tokenization.


### 8) `./scripts/clean_abc.py` 

Validate ABC files (meter, key, measures, notes, voice–metadata match), keep only valid ones, retry conversion from unsanitized MIDI to recover extras, and log remaining failures.


### 9) `./scripts/tokenize_abc.py`

Parse ABC files into per-voice token sequences (notes, chords, barlines, durations), attach instrument/category metadata from MuseScore, and log unused tokens and failures.

`encoder_decoder_utils.py` provides a way to convert between tokenized format and textual ABC file format.


### 10) `./scripts/split_abc_tracks.py`

Split multi-voice ABC files into individual per-track files by detecting `V:` sections, preserving the header, and writing one `track N.abc` per voice for easier playback and dataset verification (using [Starbound Composer](https://www.starboundcomposer.com/) (note that it needs Starbound installed) or any other ABC player).


### 11) `./scripts/build_hf_dataset.py` (optional)

Aggregate all processed MIDI-derived files into a unified Hugging Face compatible dataset by reading tokenized voices, ABC tracks, and genre labels, then exporting them as structured Parquet shards.

See [🤗 Mader ABC V2 - Music Dataset](https://huggingface.co/datasets/Gapagapi1/mader-abc-v2-music-dataset) for more information on the resulting dataset structure.


### 12) `./scripts/all_tokens.py` (optional)

Aggregate all token files across the dataset into a single vocabulary, write it to disk and print it.


### 13) `./scripts/convert_to_musicxml.py` (optional, replaces `./scripts/convert_to_abc.py`)

Same as `./convert_to_abc.sh` but for MusicXML. Note that the pipeline ends at this point if you choose this path.


### 14) `./scripts/clear_data.sh` (optional)

Clears all generated data from the pipeline, including results. Useful when the pipeline didn't finish early in the process and you want to rerun it entirely.


## 💡 Tips & Troubleshooting

* **MuseScore CLI not found?**: See the `setup_softwares.sh` section and ensure `musescore` is correctly linked to Musescore's installation directory. 
* **midi2abc errors on certain files?**: That's expected for some MIDI variants; ensure `sanitize_midi.sh` ran; if a file still fails, the cleaner script may fall back to the original MIDI in a second pass. 


## ⏳ TODO

- [ ] Double-check that ABC note tokenization produces unique tokens.
- [ ] Ensure that genre assignment is deterministic in the case of ties or ambiguous mappings.
- [ ] Remove dependencies.
- [ ] Explore further applications...


## 🪪 License

- **Code (this repository):** MIT License; see [LICENSE](./LICENSE).
- **Important:** This repo contains *code only*. Any **datasets** or **trained models** produced by this code may be subject to additional restrictions from their upstream sources (e.g., Million Song Dataset / Echo Nest terms, Tagtraum, TU Wien MAGD/MASD/TopMAGD, Lakh MIDI Dataset); consult their respective licenses if you use resulting data/models.


## 🪶 Attribution

- [Lakh MIDI Dataset](https://colinraffel.com/projects/lmd/)

> Colin Raffel. **"Learning-Based Methods for Comparing Sequences, with Applications to Audio-to-MIDI Alignment and Matching"**. PhD Thesis, 2016.


- [Million Song Dataset](http://millionsongdataset.com/)

> Thierry Bertin-Mahieux, Daniel P. W. Ellis, Brian Whitman, and Paul Lamere. **"The Million Song Dataset"**. In Proceedings of the 12th International Society for Music Information Retrieval Conference, pages 591–596, 2011.


- [Million Song Dataset Benchmarks](https://www.ifs.tuwien.ac.at/mir/msd/)

> Alexander Schindler, Rudolf Mayer and Andreas Rauber. Facilitating comprehensive benchmarking experiments on the million song dataset. In Proceedings of the 13th International Society for Music Information Retrieval Conference (ISMIR 2012), 2012. \[[pdf](http://www.ifs.tuwien.ac.at/~schindler/pubs/ISMIR2012.pdf)\]

> Alexander Schindler and Andreas Rauber. Capturing the temporal domain in Echonest Features for improved classification effectiveness. In Proceedings of the 10th International Workshop on Adaptive Multimedia Retrieval (AMR 2012) to appear, 2012. \[[pdf](http://www.ifs.tuwien.ac.at/~schindler/pubs/AMR2012.pdf)\]


- [Tagtraum genre annotations for the Million Song Dataset](https://www.tagtraum.com/msd_genre_datasets.html)

> Hendrik Schreiber. [Improving Genre Annotations for the Million Song Dataset.](https://www.tagtraum.com/download/schreiber_msdgenre_ismir2015.pdf) In Proceedings of the 16th International Society for Music Information Retrieval Conference (ISMIR), pages 241-247, Málaga, Spain, Oct. 2015. \[[slides](https://speakerdeck.com/hendriks73/improving-genre-annotations-for-the-million-song-dataset)\]


## 👥 Author Contributions

- **Julien Zébic** — [@Gapagapi1] — Project Motivation; Early Dataset Exploration; Conceptualization; Data Investigation; Software (Midi/MusicXML/ABC/Parquet Pipeline); General MIDI Instrument Categorization; Writing & Publication

  *Designed and implemented the end-to-end data pipeline (scheduler & parallel execution, MIDI to ABC conversion/cleaning, MuseScore sanitization & metadata verification / matching, MusicXML path exploration, ABC tokenization, Parquet dataset conversion); Ran experiments up to last full run and prepared the final pipeline result.*


- **Thomas Leguéré** — [@ThomasLeguere] — Early Dataset Exploration; Conceptualization; Data Investigation; Software (Genre Handling)

  *Implemented track/genre matching and mapping (including label balancing); built matching utility (`./scripts/match_tracks.py`), and related work for the genre handling part of the pipeline.*


- **Loïs Bréant** — [@loisBreant] — Data Investigation; Data Visualization

  *Implemented data rendering utilities and results used during conceptualization.*


## 📚 Citation

If this pipeline or dataset formulation helps your work, consider citing the project, the upstream datasets and the tools used.

For this project, please use the "Cite this repository" button in the about section of this repository.
