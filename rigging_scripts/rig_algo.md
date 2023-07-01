I need a place to start carving out the steps needed to get the animation working well.

# Model Scaling
## Get target segment lengths

bones could be scaled to hi

Step 2: import trajectories as empties


Step 3: Impose Bone Constraints

Primarily, I think it makes sense to use the IK constraints with a short chain (maybe just 1)

The foot tracking is sufficiently bad that it may make better sense to run Damped Tracking to the foot index from the ankle.

    