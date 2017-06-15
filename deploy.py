import boto3
from datetime import datetime
import sys
import docker
import random

def ecs_deploy(cmd):

    port = int(random.uniform(3000, 30000))
    print 'port: ' + str(port)

    family = 'viz-backend-task'

    containerDefinitions = [{
                            'name': 'viz-backend',
                            'image': '637630236727.dkr.ecr.us-west-2.amazonaws.com/rosindustrial/viz:debug',
                            'cpu': 1024,
                            'memory': 3000,
                            'portMappings': [
                                {
                                    'containerPort': 9090,
                                    'hostPort': port,
                                    'protocol': 'tcp'
                                },
                            ],
                            'essential': True,
                            'command': cmd,
                            'hostname':'rosbackend',
                            'privileged':True
                            }]


    client = boto3.client('ecs', region_name='us-west-2')

    register_response = client.register_task_definition(family=family,
                                               containerDefinitions=containerDefinitions)

    instances = client.list_container_instances(status='ACTIVE')

    if register_response['ResponseMetadata']['HTTPStatusCode']==200:
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

    print datetime.utcnow()
    start_response = client.start_task(taskDefinition=taskDef,
                                       containerInstances=instance_arn)

    print 'start response: '
    print start_response
    return port

def local_deploy(cmd):
    client = docker.from_env()
    port = 9090
    print client.containers.run('637630236727.dkr.ecr.us-west-2.amazonaws.com/rosindustrial/viz:debug',
                                cmd,
                                detach=True,
                                network_mode='host',
                                ports={'9090/tcp': port})
    return port

def fake_deploy(cmd):
    port = 9090
    return port

def local_build(branch, owner, repo, package, launch_file):
    repo.remote()
    client = docker.from_env()
    cmd = ['/bin/bash', '-cl',
           'source /opt/ros/kinetic/setup.bash && '
           'git clone -b {} https://github.com/{}/{} /workspace/src/{} && '
           'catkin build --workspace /workspace && '
           'python2 launch_maker.py {} {}'.format(branch, owner, repo, repo, package, launch_file)]
    print cmd
    print client.containers.run('637630236727.dkr.ecr.us-west-2.amazonaws.com/rosindustrial/viz:debug',
                                cmd,
                                detach=True,
                                network_mode='host')
    return hash