#%%

from pathlib import Path
import os
import toml
import csv
import bpy
# import polars as pl

print(__file__)
__root__ = Path(__file__).parent.parent

processed_folder = Path(__root__, "HOLISTIC_OPENSIM")

config_path = Path(processed_folder, "config.toml")
config_dict = toml.load(config_path)

fps = config_dict["fps_recording"]

trajectory_data_path = Path(processed_folder, "xyz_HOLISTIC_OPENSIM_labelled.csv")


#%%
# load in trajectory data
# Create an empty list to hold the data
data = []
# Open the CSV file and process the inputs one by one
with open(trajectory_data_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)


#%%
# create a list of all the empties that need to get populated in the animation
all_columns = list(data[0].keys())
empty_names = [field_name[0:-2] for field_name in all_columns if field_name[-2:] == "_x"]
print(f"Empty names are {empty_names}")

# test run of inserting a trajectory and moving it around
# choosing "right_wrist"
empty_name = "right_wrist"
bpy.ops.object.empty_add(type='PLAIN_AXES')
empty = bpy.context.object
empty.name = empty_name

for frame in data:
    sync_index = int(frame["sync_index"])
    x = frame[f"{empty_name}_x"]
    y = frame[f"{empty_name}_y"]
    z = frame[f"{empty_name}_z"]

    if x != '':    
        x = float(x)
        y = float(y)
        z = float(z)

        empty.location = (x,y,z)
        empty.keyframe_insert(data_path='location', frame = sync_index)



# trajectory_data = pl.read_csv(trajectory_data_path)

# trajectory_data = trajectory_data.with_columns([
#     (pl.col("sync_index")*(1/fps)).alias("time"), 
# ])

# %%
# empty_column_data = [col for col in trajectory_data.columns if col[-2:] in ("_x", "_y", "_z")]
# %%
