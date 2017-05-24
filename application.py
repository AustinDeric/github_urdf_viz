from flask import Flask, url_for, render_template
import requests
import json
from pathlib import PurePath
import deploy
import time

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# add a rule for the index page.
@application.route('/')
def index():
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
                new_path = url_for('urdfviz',
                                   owner=owner, repo=repo,
                                   branch=branch, robot=robot_name)
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
        #find launch folder in packages
        if PurePath(i['path']).suffix == '.launch':
            #find robot from launch file
            if ((PurePath(i['path']).stem)[0:5] == 'load_'):
                if PurePath(i['path']).stem[5:] == robot:
                    print "path:" + i['path']
                    launch_file = PurePath(i['path']).name
                    print 'launch_file: ' + launch_file
                    package = PurePath(i['path']).parts[0]
                    print 'package: ' + package
        # find launch folder in packages
        if len(PurePath(i['path']).parts)>3:
            if PurePath(i['path']).parts[1] == 'meshes':
                if PurePath(i['path']).parts[3] == 'visual':
                    if PurePath(i['path']).suffix =='.stl':
                        print PurePath(i['path'])
                        mesh_type = 'THREE.STLLoader'
                    if PurePath(i['path']).suffix =='.dae':
                        mesh_type = 'ROS3D.COLLADA_LOADER_2'

    #add package failure message
    if not package:
        return url_for('page_not_found')
    if not launch_file:
        return url_for('page_not_found')
    if not mesh_type:
        return url_for('page_not_found')


    github_url = 'https://github.com/{}/{}/tree/{}/{}'.format(owner, repo, branch, package)
    mesh_url = 'https://raw.githubusercontent.com/{}/{}/{}/'.format(owner,
                                                                    repo, branch)

    # docker stuff
    cmd = ['/bin/bash', '-c',
           'source /opt/ros/kinetic/setup.bash && '
           'git clone -b {} https://github.com/{}/{} /workspace/src/{} && '
           'catkin build --workspace /workspace && '
           'source /workspace/devel/setup.bash && '
           'python2 launch_maker.py {} {} && '
           'roslaunch viz.launch'.format(branch, owner, repo, repo,
                                         package, launch_file)]

    print 'command:'
    print cmd
    time.sleep(15)
    url_ros_backend = deploy.ecs_deploy(cmd=cmd)

    return render_template('viz.html',
                           robot_name=robot, mesh_url=mesh_url,
                           launch_file=launch_file, url_ros_backend=url_ros_backend,
                           mesh_type=mesh_type, github_url=github_url)

@application.route('/test')
def test_url():
    return render_template('rosbridge_test.html')

@application.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

# run the app.
if __name__ == "__main__":
    application.debug = False
    application.run()