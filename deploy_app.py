import deploy

owner = 'gavanderhoorn'
repo = 'abb_experimental'
branch = 'irb52_mention_variants'
package = ' abb_irb52_support'
launch_file = 'load_irb52_7_145.launch'

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
deploy.fake_deploy(cmd=cmd)
