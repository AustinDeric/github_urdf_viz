import boto3
from datetime import datetime
import sys

def ros_command(cmd):
    return '/bin/bash -c "source /opt/ros/kinetic/setup.bash && {}"'.format(cmd)

def workspace_command(cmd):
    return ros_command('/bin/bash -c "source /workspace/devel/setup.bash && {}"'.format(cmd))

owner = 'AustinDeric'
repo = 'abb_experimental'
branch = 'irb1600-dae'
launch_file_rel_path = 'abb_irb1600_support/launch/load_irb1600_6_12.launch'

cmds = []
cmds.append('/viz_entrypoint.sh')
cmds.append('git clone -b {} https://github.com/{}/{} /workspace/src/{}'.format(branch, owner, repo, repo))
cmds.append(ros_command('catkin build --workspace /workspace'))
cmds.append(workspace_command('roslaunch /workspace/src/{}/{}'.format(repo, launch_file_rel_path)))
print 'commands: '
print cmds

#ECS setup
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
                        'command': cmds,
                        'logConfiguration':
                            {
                                'logDriver': 'json-file'
                            }
                        }]


client = boto3.client('ecs')

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