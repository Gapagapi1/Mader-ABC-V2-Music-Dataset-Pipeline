from datasets import load_dataset
from datasets import ClassLabel
from datasets import DatasetDict

def upload_ds(ds_name: str):
    ds = load_dataset(
        "parquet",
        data_files={"train": f"./data/{ds_name}/*.parquet"},
        split="train",
    )
    print(ds)
    print(ds.features)

    INSTRUMENTS = ["Piano", "Organ", "Guitar", "Bass", "String", "Vocal", "Brass", "Reed", "Pipe", "Synth Lead", "Synth Pad", "Synth Effect", "Pitched Percussion", "Percussive", "Sound Effect", "Percussion Channel"]
    instrument_label = ClassLabel(names=INSTRUMENTS)

    GENRES = ["Rock", "Pop", "Electronic", "Country", "RnB", "Jazz", "World", "Other", "Unknown"]
    genre_label = ClassLabel(names=GENRES)

    features = ds.features.copy()
    features["instrument_category"] = instrument_label
    features["genre_category"] = genre_label

    ds_cast = ds.cast(features)
    print(ds_cast.features)

    dset = DatasetDict({"train": ds_cast})

    dset.push_to_hub("Gapagapi1/Mader-ABC-V2-Music-Dataset", config_name=ds_name)

upload_ds("abc_tokens")
upload_ds("abc_texts")

