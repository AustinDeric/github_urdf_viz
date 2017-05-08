from flask import Flask
from flask import render_template
import requests
import json
import time
import docker
from pathlib import PurePath
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
    cont = client.containers.run('rosindustrial/viz:kinetic', '/bin/bash -c "source /opt/ros/kinetic/setup.bash && roslaunch viz.launch"', detach=True, network_mode='host', publish_all_ports=True)
    cont.exec_run('mkdir /workspace/src/{}'.format(repo))
    cont.exec_run('git clone -b {} https://github.com/{}/{} /workspace/src/{}'.format(branch, owner, repo, repo))
    cont.exec_run('/bin/bash -c "source /opt/ros/kinetic/setup.bash && catkin build --workspace /workspace"')
    cmd = '/bin/bash -c "source /opt/ros/kinetic/setup.bash && source /workspace/devel/setup.bash && roslaunch /workspace/src/{}/{}"'.format(repo, launch_file_rel_path)
    cont.exec_run(cmd)
    return render_template('viz.html', robot_name=robot, mesh_url=mesh_url)

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()