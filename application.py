from flask import Flask, url_for, render_template
import requests
import json
from pathlib import PurePath
import deploy
import sys
import time

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# add a rule for the index page.
@application.route('/')
def root_index():
    return render_template('index.html')

@application.route('/<owner>/<repo>/<branch>')
def list_robots(owner=None, repo=None, branch=None):
    sha_url = 'https://api.github.com/repos/{}/{}/branches/{}'.format(owner, repo, branch)
    r = requests.get(sha_url)
    sha_data = json.loads(r.text)
    sha = sha_data['commit']['sha']

    tree_payload = {'recursive': '1'}
    tree_url = 'https://api.github.com/repos/{}/{}/git/trees/{}'.format(owner, repo, sha)
    x = requests.get(tree_url, tree_payload)
    tree_data = json.loads(x.text)
    robots = []
    for i in tree_data['tree']:
        if PurePath(i['path']).suffix == '.launch':
            if ((PurePath(i['path']).stem)[0:5] == 'load_'):
                robot_name = PurePath(i['path']).stem[5:]
                new_path = url_for('urdfviz', owner=owner, repo=repo, branch=branch, robot=robot_name)
                robots.append({'href': new_path, 'caption': robot_name})

    return render_template('list_robots.html', robots=robots)

@application.route('/<owner>/<repo>/<branch>/<robot>')
def urdfviz(owner=None, repo=None, branch=None, robot=None):

    # find mesh url to load
    sha_url = 'https://api.github.com/repos/{}/{}/branches/{}'.format(owner, repo, branch)
    r = requests.get(sha_url)
    print r
    sha_data = json.loads(r.text)
    sha = sha_data['commit']['sha']

    tree_payload = {'recursive': '1'}
    tree_url = 'https://api.github.com/repos/{}/{}/git/trees/{}'.format(owner, repo, sha)
    x = requests.get(tree_url, tree_payload)
    tree_data = json.loads(x.text)
    for i in tree_data['tree']:
        if PurePath(i['path']).suffix == '.launch':
            if ((PurePath(i['path']).stem)[0:5] == 'load_'):
                if PurePath(i['path']).stem[5:] == robot:
                    print "path:" + i['path']
                    launch_file = PurePath(i['path']).name
                    print 'launch_file: ' + launch_file
                    package = PurePath(i['path']).parts[0]
                    print 'package: ' + package

    #add package failure message
    if not package:
        sys.exit("package not found")

    mesh_url = 'https://raw.githubusercontent.com/{}/{}/{}/'.format(owner, repo, branch)

    # docker stuff
    cmd = ['/bin/bash', '-cl',
           'source /opt/ros/kinetic/setup.bash && '
           'git clone -b {} https://github.com/{}/{} /workspace/src/{} && '
           'catkin build {} --workspace /workspace && '
           'source /workspace/devel/setup.bash && '
           'python2 launch_maker.py {} {} && '
           'roslaunch viz.launch'.format(branch, owner, repo, repo, package, package, launch_file)]

    port = deploy.ecs_deploy(cmd=cmd)

    time.sleep(15)
    url_ros_backend = 'ws://34.210.216.142:{}'.format(port)

    return render_template('viz.html',
                           robot_name=robot,
                           mesh_url=mesh_url,
                           launch_file=launch_file,
                           url_ros_backend=url_ros_backend)

@application.route('/test')
def test_url():
    return render_template('rosbridge_test.html')

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()