# Needs ROS2 Foxy on Ubuntu 20.04

# Build and Run


`colcon build --packages-select d1_550_description`
`source install/setup.bash`

`killall gzserver gzclient 2>/dev/null; sleep 2`
`ros2 launch d1_550_description gazebo.launch.py`

In a new terminal run this bridger for the slider control

`source /opt/ros/foxy/setup.bash`
`source ~/ros2_ws/install/setup.bash`
`python3 ~/ros2_ws/slider_bridge.py`
