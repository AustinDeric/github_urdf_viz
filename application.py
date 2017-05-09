from flask import Flask
from flask import render_template
import requests
import json
import time
import docker
from pathlib import PurePath

def ros_command(cmd):
    return '/bin/bash -c "source /opt/ros/kinetic/setup.bash && {}"'.format(cmd)

def workspace_command(cmd):
    return ros_command('/bin/bash -c "source /workspace/devel/setup.bash && {}"'.format(cmd))

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
                new_path = 'localhost:5000/{}/{}/{}/{}'.format(owner, repo, branch, robot_name)
                robots.append({'href': new_path, 'caption': robot_name})

    return render_template('list_robots.html', robots=robots)

@application.route('/<owner>/<repo>/<branch>/<robot>')
def urdfviz(owner=None, repo=None, branch=None, robot=None):

    # web stuff
    sha_url = 'https://api.github.com/repos/{}/{}/branches/{}'.format(owner, repo, branch)
    r = requests.get(sha_url)
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
                    launch_file_rel_path = i['path']
    mesh_url = 'https://raw.githubusercontent.com/{}/{}/{}/'.format(owner, repo, branch)

    #docker stuff
    client = docker.from_env()
    port_dict = {'9090/tcp': '9090'}
    cmds=[]
    cmds.append('mkdir /workspace/src/{}'.format(repo))
    cmds.append('git clone -b {} https://github.com/{}/{} /workspace/src/{}'.format(branch, owner, repo, repo))
    cmds.append(ros_command('roslaunch viz.launch'))
    cmds.append(ros_command('catkin build --workspace /workspace'))
    cmds.append(workspace_command('roslaunch /workspace/src/{}/{}'.format(repo, launch_file_rel_path)))
    cont = client.containers.run('rosindustrial/viz:kinetic',
                                 cmds,
                                 detach=True,
                                 network_mode='host',
                                 ports=port_dict)

    return render_template('viz.html', robot_name=robot, mesh_url=mesh_url)

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()