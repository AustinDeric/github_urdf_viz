from flask import Flask, url_for, render_template
import requests
import json
from pathlib import PurePath
import random
import boto3
import sys



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
                new_path = url_for('local_urdfviz', owner=owner, repo=repo, branch=branch, robot=robot_name)
                robots.append({'href': new_path, 'caption': robot_name})

    return render_template('list_robots.html', robots=robots)

@application.route('/l/<owner>/<repo>/<branch>/<robot>')
def local_urdfviz(owner=None, repo=None, branch=None, robot=None):

    # find mesh url to load
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
                    launch_file = PurePath(i['path']).name
                    print 'launch_file: ' + launch_file
                    package = PurePath(i['path']).root
                    print 'package: ' + package

    mesh_url = 'https://raw.githubusercontent.com/{}/{}/{}/'.format(owner, repo, branch)
    #generate random port

    url_ros_backend = 'ws://localhost:9090'

    return render_template('viz.html', robot_name=robot, mesh_url=mesh_url, url_ros_backend=url_ros_backend)

@application.route('/r/<owner>/<repo>/<branch>/<robot>')
def remote_urdfviz(owner=None, repo=None, branch=None, robot=None):

    # find mesh url to load
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
                    launch_file = PurePath(i['path']).name
                    print 'launch_file: ' + launch_file
                    package = PurePath(i['path']).root
                    print 'package: ' + package

    mesh_url = 'https://raw.githubusercontent.com/{}/{}/{}/'.format(owner, repo, branch)

    url_ros_backend = 'ws://52.89.93.213:9090'

    return render_template('viz.html', robot_name=robot, mesh_url=mesh_url, url_ros_backend=url_ros_backend)

@application.route('/test')
def test_url():
    return render_template('rosbridge_test.html')

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()