def create_launch_file(package, launch_file):
    lines = []
    lines.append('<launch>')
    lines.append('<include file="$(find rosbridge_server)/launch/rosbridge_websocket.launch" />')
    lines.append('<node name="tf2_web_republisher" pkg="tf2_web_republisher" type="tf2_web_republisher"/>')
    lines.append('<node name="robot_state_publisher" pkg="robot_state_publisher" type="state_publisher" />')
    lines.append('<node name="joint_state_publisher" pkg="joint_state_publisher" type="joint_state_publisher"/>')
    lines.append('<include file="$(find {})/launch/{}" />'.format(package, launch_file))
    lines.append('</launch>')
    f = open('viz.launch','w')
    for line in lines:
        f.write('{}\n'.format(line))

if __name__ == "__main__":
    import sys
    create_launch_file(str(sys.argv[1]), str(sys.argv[2]))