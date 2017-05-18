import docker
def ros_command(cmd):
    return '/bin/bash -c "source /opt/ros/kinetic/setup.bash && {}"'.format(cmd)

def workspace_command(cmd):
    return ros_command('/bin/bash -c "source /workspace/devel/setup.bash && {}"'.format(cmd))

client = docker.from_env()

owner = 'AustinDeric'
repo = 'abb_experimental'
branch = 'irb1600-dae'
package = 'abb_irb1600_support'
launch_file = 'load_irb1600_6_12.launch'

# docker stuff
cmds = []
cmds.append('git clone -b {} https://github.com/{}/{} /workspace/src/{}'.format(branch, owner, repo, repo))
cmds.append('catkin build --workspace /workspace')
cmds.append('source /workspace/devel/setup.bash')
cmds.append('python2 launch_maker.py {} {}'.format(package, launch_file))
cmds.append('roslaunch viz.launch')
cmd = '{} && {} && {} && {} && {}'.format(cmds[0], cmds[1], cmds[2], cmds[3], cmds[4])
print 'commands: '
cmd = '/bin/bash -c "source /opt/ros/kinetic/setup.bash && git clone -b irb1600-dae https://github.com/AustinDeric/abb_experimental /workspace/src/abb_experimental && catkin build --workspace /workspace && source /workspace/devel/setup.bash && python2 launch_maker.py abb_irb1600_support load_irb1600_6_12.launch && roslaunch viz.launch"'
client = docker.from_env()
print client.containers.run('637630236727.dkr.ecr.us-west-2.amazonaws.com/rosindustrial/viz:latest', cmd, detach=True,
                             network_mode='host', publish_all_ports=True).logs()