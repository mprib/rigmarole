# rigmarole

This is a companion project to [pyxy3d](https://github.com/mprib/pyxy3d). It is currently in a very early state. The code here is intended to be run within Blender, allowing the core motion tracking output to be used as the basis of developing animated rigs. My thought is that as this project matures it could become an add-on for Blender.

I still have much to learn on that front and am very open to help on this from the Blender animation community.

The video below demonstrates the basic process:

1. A human rig is created so that it's segments will scale with the lengths of the segments estimated via markerless 3D tracking.
2. Empty trajectories are imported that correspond to the tracked 3D trajectories of joint and face landmarks.
3. Inverse Kinematics are applied to animate the rig.
4. The rig animation is baked.