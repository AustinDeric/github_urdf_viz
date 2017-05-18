import boto3
from datetime import datetime
import json
import sys

def ros_command(cmd):
    return '/bin/bash -c "source /opt/ros/kinetic/setup.bash && {}"'.format(cmd)

def workspace_command(cmd):
    return ros_command('/bin/bash -c "source /workspace/devel/setup.bash && {}"'.format(cmd))

owner = 'AustinDeric'
repo = 'abb_experimental'
branch = 'irb1600-dae'
package = 'abb_irb1600_support'
launch_file = 'load_irb1600_6_12.launch'

# docker stuff
#cmds = []
#cmds.append('git clone -b {} https://github.com/{}/{} /workspace/src/{}'.format(branch, owner, repo, repo))
#cmds.append('catkin build --workspace /workspace')
#cmds.append('source /workspace/devel/setup.bash')
#cmds.append('python2 launch_maker.py {} {}'.format(package, launch_file))
#cmds.append('roslaunch viz.launch')
#cmd = '{} && {} && {} && {} && {}'.format(cmds[0], cmds[1], cmds[2], cmds[3], cmds[4])
print 'commands: '
#cmd = '/bin/bash','-c','source','/opt/ros/kinetic/setup.bash','&&','git','clone','-b','irb1600-dae','https://github.com/AustinDeric/abb_experimental','/workspace/src/abb_experimental','&&','catkin','build','--workspace','/workspace','&&','source','/workspace/devel/setup.bash','&&','python2','launch_maker.py','abb_irb1600_support','load_irb1600_6_12.launch','&&','roslaunch','viz.launch'
cmd = ['/bin/bash','-c','source /opt/ros/kinetic/setup.bash && git clone -b irb1600-dae https://github.com/AustinDeric/abb_experimental /workspace/src/abb_experimental && catkin build --workspace /workspace && source /workspace/devel/setup.bash && python2 launch_maker.py abb_irb1600_support load_irb1600_6_12.launch && roslaunch viz.launch']
print cmd

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
                        'command': cmd,
                        'entryPoint': []
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