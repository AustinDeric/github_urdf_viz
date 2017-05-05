from flask import Flask
from flask import render_template
import requests
import json
from pathlib import PurePath
import docker
import time

app = Flask(__name__)

def ros_command(cmd=None):
    return '/bin/bash -c "source /opt/ros/kinetic/setup.bash && {}"'.format(cmd)

def workspace_command(cmd=None):
    return ros_command('source /workspace/devel/setup.bash && {}'.format(cmd))

@app.route('/<owner>/<repo>/<branch>')
def list_robots(owner=None, repo=None, branch=None):

    sha_url = 'https://api.github.com/repos/{}/{}/branches/{}'.format(owner, repo, branch)
    r = requests.get(sha_url)
    print('sha url: ' + r.url)
    print('sha status code: ' + str(r.status_code))
    sha_data = json.loads(r.text)
    sha = sha_data['commit']['sha']

    tree_payload = {'recursive': '1'}
    tree_url = 'https://api.github.com/repos/{}/{}/git/trees/{}'.format(owner, repo, sha)
    x = requests.get(tree_url, tree_payload)
    print('tree url: ' + r.url)
    print('tree status code: ' + str(x.status_code))
    tree_data = json.loads(x.text)
    robots = []
    for i in tree_data['tree']:
        if PurePath(i['path']).suffix=='.launch':
            if((PurePath(i['path']).stem)[0:5]=='load_'):
                robot_name = PurePath(i['path']).stem[5:]
                new_path = 'localhost:5000/{}/{}/{}/{}'.format(owner, repo, branch, robot_name)
                robots.append({'href': new_path, 'caption': robot_name})

    return render_template('list_robots.html', robots=robots)

@app.route('/<owner>/<repo>/<branch>/<robot>')
def urdfviz(owner=None, repo=None, branch=None, robot=None):

    # web stuff
    sha_url = 'https://api.github.com/repos/{}/{}/branches/{}'.format(owner, repo, branch)
    r = requests.get(sha_url)
    print('sha url: ' + r.url)
    print('sha status code: ' + str(r.status_code))
    sha_data = json.loads(r.text)
    sha = sha_data['commit']['sha']

    tree_payload = {'recursive': '1'}
    tree_url = 'https://api.github.com/repos/{}/{}/git/trees/{}'.format(owner, repo, sha)
    x = requests.get(tree_url, tree_payload)
    print('tree url: ' + x.url)
    print('tree status code: ' + str(x.status_code))
    tree_data = json.loads(x.text)
    for i in tree_data['tree']:
        if PurePath(i['path']).suffix == '.launch':
            if ((PurePath(i['path']).stem)[0:5] == 'load_'):
                if PurePath(i['path']).stem[5:] == robot:
                    launch_file_rel_path = i['path']
    mesh_url = 'https://raw.githubusercontent.com/{}/{}/{}/'.format(owner, repo, branch)

    #docker stuff
    t = time.time()
    client = docker.from_env()
    cont = client.containers.run('rosindustrial/viz:kinetic', ros_command('roslaunch viz.launch'), detach=True, network_mode='host', publish_all_ports=True)
    time.sleep(3)
    print('----------------')
    print('ps -ef')
    print(cont.exec_run(ros_command('ps -ef')))
    print('----------------')
    print('rostopic list')
    print(cont.exec_run(ros_command('rostopic list')))
    print('----------------')
    print('mkdir')
    print(cont.exec_run('mkdir /workspace/src/{}'.format(repo)))
    print('----------------')
    print('git clone')
    print(cont.exec_run('git clone -b {} https://github.com/{}/{} /workspace/src/{}'.format(branch, owner, repo, repo)))
    print('----------------')
    print('catkin build')
    print(cont.exec_run(ros_command('catkin build --workspace /workspace')))
    print('----------------')
    print('roslaunch')
    cmd = workspace_command('roslaunch /workspace/src/{}/{}'.format(repo, launch_file_rel_path))
    print(cont.exec_run(cmd))
    print('----------------')
    print('rosparam')
    print(cont.exec_run(ros_command('rosparam get /robot_description')))
    print('----------------')
    print('ps -ef')
    print(cont.exec_run(ros_command('ps -ef')))
    print('----------------')
    print('rostopic list')
    print(cont.exec_run(ros_command('rostopic list')))


    print('elapsed time: ' + str(time.time() - t))


    return render_template('viz.html', robot_name=robot, mesh_url=mesh_url)

# run the app.
if __name__ == "__main__":
    app.run()