from flask import Flask, url_for, render_template
import requests
import json
from pathlib import PurePath
import random

#def ros_command(cmd):
#    return '/bin/bash -c "source /opt/ros/kinetic/setup.bash && {}"'.format(cmd)

#def workspace_command(cmd):
#    return ros_command('/bin/bash -c "source /workspace/devel/setup.bash && {}"'.format(cmd))

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# add a rule for the index page.
@application.route('/')
def root_index():
    '''
    owner_names = ['AustinDeric', 'Jmeyer1292', 'gavanderhoorn', 'geoffreychiou', 'Levi-Armstrong', 'shaun-edwards', 'VictorLamoine']
    owner = {}
    for i in owner_names:
        owner['owner_name']= i
        owner['owner_name'] = i
    '''
    return render_template('index.html')


# add a rule for the index page.
#@application.route('/<owner>')
#def owner_page(owner=None):


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
    #generate random port
    port = random.uniform(1, 10)

    #container commands

    return render_template('viz.html', robot_name=robot, mesh_url=mesh_url)

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()