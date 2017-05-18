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
                    launch_file = PurePath(i['path']).name
                    print 'launch_file: ' + launch_file
                    package = PurePath(i['path']).root
                    print 'package: ' + package

    mesh_url = 'https://raw.githubusercontent.com/{}/{}/{}/'.format(owner, repo, branch)
    #generate random port

    port = int(random.uniform(100, 65000))
    print 'port: ' + str(port)

    # docker stuff
    cmd = ['/bin/bash', '-c',
           'source /opt/ros/kinetic/setup.bash && git clone -b {} https://github.com/{}/{} /workspace/src/{} && catkin build --workspace /workspace && source /workspace/devel/setup.bash && python2 launch_maker.py {} {} && roslaunch viz.launch'.format(
               branch, owner, repo, repo, package, launch_file)]
    print 'commands: '
    print cmd

    # docker stuff
    cmd = ['/bin/bash', '-c',
           'source /opt/ros/kinetic/setup.bash && git clone -b {} https://github.com/{}/{} /workspace/src/{} && catkin build --workspace /workspace && source /workspace/devel/setup.bash && python2 launch_maker.py {} {} && roslaunch viz.launch'.format(
               branch, owner, repo, repo, package, launch_file)]
    print 'commands: '
    print cmd

    # ECS setup
    family = 'viz-backend-task'

    containerDefinitions = [{
        'name': 'viz-backend',
        'image': '637630236727.dkr.ecr.us-west-2.amazonaws.com/rosindustrial/viz:latest',
        'cpu': 512,
        'memory': 300,
        'portMappings': [
            {
                'containerPort': 9090,
                'hostPort': 9090,
                'protocol': 'tcp'
            },
        ],
        'essential': True,
        'command': cmd,
        'entryPoint': []
    }]

    client = boto3.client('ecs')

    register_response = client.register_task_definition(family=family,
                                                        containerDefinitions=containerDefinitions)

    instances = client.list_container_instances(status='ACTIVE')

    if register_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        req_arn = register_response['taskDefinition']['taskDefinitionArn']
        req_family = register_response['taskDefinition']['family']
        req_rev = register_response['taskDefinition']['revision']
        print 'taskDefinition:'
        print register_response['taskDefinition']
        print 'arn:'
        print req_arn
        print 'family:'
        print req_family
        print 'revision:'
        print req_rev

    else:
        sys.exit(1)

    instance_arn = instances['containerInstanceArns']
    print 'containerInstanceArns:'
    print instances['containerInstanceArns']

    taskDef = '{}:{}'.format(req_family, req_rev)
    arn = []
    arn.append(str(req_arn))

    start_response = client.start_task(taskDefinition=taskDef,
                                       containerInstances=instance_arn)

    print 'start response: '
    print start_response

    url_ros_backend = ':'+ str(port)



    return render_template('viz.html', robot_name=robot, mesh_url=mesh_url)

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()