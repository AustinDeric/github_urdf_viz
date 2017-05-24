import deploy

owner = 'AustinDeric'
repo = 'abb_experimental'
branch = 'irb1600-dae'
package = 'abb_irb1600_support'
launch_file = 'load_irb1600_6_12.launch'

# docker stuff
cmd = ['/bin/bash','-cl',
       'source /opt/ros/kinetic/setup.bash && '
             'git clone -b {} https://github.com/{}/{} /workspace/src/{} && '
             'catkin build --workspace /workspace && '
             'source /workspace/devel/setup.bash && '
             'python2 launch_maker.py {} {} && '
             'roslaunch viz.launch'.format(branch, owner, repo, repo, package, launch_file)]
print 'cmd'
print cmd
deploy.local_deploy(cmd=cmd)
