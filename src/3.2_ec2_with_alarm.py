#!/usr/bin/env python3
import boto3
import time
import json
import os
import sys

ec2 = boto3.resource('ec2')
cw = boto3.client('cloudwatch')
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
vpc_info_path = os.path.join(parent_dir, "vpc_info.json")
sg_id = None
if os.path.exists(vpc_info_path):
    try:
        with open(vpc_info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            sg_id = data.get("sg_id")
            public_subnets = data.get("public_subnets")
            private_subnets = data.get("private_subnets")
    except (json.JSONDecodeError, IOError):
        print(f"Error reading JSON from {vpc_info_path}")
else:
    print(f"No vpc_info.json found at {vpc_info_path}")

if not sg_id:
    print("vpc_id not found in vpc_info.json. Exiting.")
    sys.exit(1)

# IAM Role LabRole


# Launch 4 instances
subnets = public_subnets+private_subnets  # CHANGE
#sg_id = 'sg-0yourSGid'  # CHANGE
role_name = "LabRole"

for i, subnet in enumerate(subnets):
    instance = ec2.create_instances(
        ImageId='ami-0ecb62995f68bb549',  # Amazon Linux 2
        InstanceType='t3.micro',
        MinCount=1, MaxCount=1,
        SubnetId=subnet,
        SecurityGroupIds=[sg_id],
        KeyName='polystudent-pair',
        TagSpecifications=[{'ResourceType':'instance','Tags':[{'Key':'Name','Value':f'tp4-ec2-{i}'}]}]
    )[0]

    # CloudWatch Alarm: NetworkIn > 1000 packets/sec
    cw.put_metric_alarm(
        AlarmName=f'High-Ingress-Packets-{instance.id}',
        MetricName='NetworkIn',
        Namespace='AWS/EC2',
        Statistic='Average',
        Period=300,
        EvaluationPeriods=2,
        Threshold=1000,
        ComparisonOperator='GreaterThanThreshold',
        Dimensions=[{'Name':'InstanceId','Value':instance.id}],
        AlarmActions=[]  # optional SNS
    )
    print(f"Instance {instance.id} launched with alarm")