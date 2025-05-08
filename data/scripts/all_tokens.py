import os
import pickle

def get_all_tokens(from_path:str):
    tokens = set()

    num_folders = len(os.listdir(from_path))
    i = 0

    for root, _, files in os.walk(from_path):
        for file in files:
            if file.endswith('.pkl') or file.endswith('.pickle'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        obj = pickle.load(f)
                        tokens.update(obj)
                except Exception as e:
                    print(f"Failed to load {file_path}: {e}")
        if len(files) == 0:
            i += 1
            if i % 100 == 0:
                print("Processing: {}/{}".format(i, num_folders))

    return tokens


if __name__ == "__main__":
    if False:
        tokens = get_all_tokens("./midi/lmd_matched_flat_sanitized_abc_clean_tokenized")

        with open("results/all_tokens.pkl", "wb") as tokens_file:
            pickle.dump(tokens, tokens_file)

    if True:
        with open("results/all_tokens.pkl", "rb") as tokens_file:
            tokens = pickle.load(tokens_file)

        print(tokens)
