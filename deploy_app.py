import deploy

owner = 'ros-industrial'
repo = 'abb'
branch = 'kinetic-devel'
package = 'abb_irb6600_support'
launch_file = 'load_irb6600_225_255.launch'

# docker stuff
cmd = ['/bin/bash', '-c',
       'source /opt/ros/kinetic/setup.bash && '
       'git clone -b {} https://github.com/{}/{} /workspace/src/{} && '
       'catkin build --workspace /workspace && '
       'source /workspace/devel/setup.bash && '
       'python2 launch_maker.py {} {} && '
       'roslaunch viz.launch'.format(branch, owner, repo, repo,
                                     package, launch_file)]

print 'cmd:'
print cmd
print 'end point: ' + 'localhost:5000/owner/'
print deploy.local_deploy(cmd=cmd)
