from importlib import reload
import import_empties
reload(import_empties)
import holistic_model
reload(holistic_model)
from holistic_model import HolisticModel, clear_scene
from import_empties import import_empties, set_rig_to_anchor, create_anchor
import csv
import time
from pathlib import Path
import toml

clear_scene()
scale_json = r"C:\Users\Mac Prible\repos\rigmarole\sample\metarig_config_HOLISTIC_OPENSIM.json"
model = HolisticModel("test")
model.scale_to_config(scale_json)

processed_folder = Path(r"C:\Users\Mac Prible\OneDrive\pyxy3d\4_cam_A\recording_4\HOLISTIC_OPENSIM")

config_path = Path(processed_folder, "config.toml")
config_dict = toml.load(config_path)

fps = config_dict["fps_recording"]

trajectory_data_path = Path(processed_folder, "xyz_HOLISTIC_OPENSIM_labelled.csv")

# clear_scene()

# load in trajectory data
# Create an empty list to hold the data
data = []
print(f"beginning to load csv data at {time.time()}")
with open(trajectory_data_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)
print(f"Completing load of csv data at {time.time()}")

import_empties(data)

rig_anchors = ["right_hip", "left_hip"]
track_to_anchor = rig_anchors[0]

create_anchor(rig_anchors,track_to_anchor, data)
set_rig_to_anchor(model)