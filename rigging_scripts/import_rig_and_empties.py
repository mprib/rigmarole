
from pathlib import Path
import os
import toml
import time
import csv
import bpy
import sys

script_folder = Path(__file__).parent
sys.path.insert(0, str(script_folder))
print(f"SysPath is: {sys.path}")

from blender_functions import clear_scene, export_empties, get_human_rig

processed_folder = Path(r"C:\Users\Mac Prible\OneDrive\pyxy3d\4_cam\recording_1\HOLISTIC_OPENSIM")

config_path = Path(processed_folder, "config.toml")
config_dict = toml.load(config_path)

fps = config_dict["fps_recording"]

trajectory_data_path = Path(processed_folder, "xyz_HOLISTIC_OPENSIM_labelled.csv")

clear_scene()
# load in trajectory data
# Create an empty list to hold the data
data = []
# Open the CSV file and process the inputs one by one
print(f"beginning to load csv data at {time.time()}")
with open(trajectory_data_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)
print(f"Completing load of csv data at {time.time()}")

export_empties(data)

metahuman = get_human_rig()