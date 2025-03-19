import os
import sys
import shutil

sys.path.append(os.path.dirname("scripts"))
from data_pipeline_lib import Process


def process_function(from_path: str, to_path: str):
    shutil.copy2(from_path, to_path)


process = Process("flatten", "./midi/lmd_matched", "./midi/lmd_matched_flat")
process.step_by_function(process_function)