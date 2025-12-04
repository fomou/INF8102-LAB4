#!/usr/bin/env python3
import boto3
import json
import os
import sys

ec2 = boto3.client('ec2')
iam = boto3.client('iam')
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
vpc_info_path = os.path.join(parent_dir, "vpc_info.json")
account_id = boto3.client('sts').get_caller_identity().get('Account')

vpc_id = None
if os.path.exists(vpc_info_path):
    try:
        with open(vpc_info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            vpc_id = data.get("vpc_id")
    except (json.JSONDecodeError, IOError):
        print(f"Error reading JSON from {vpc_info_path}")
else:
    print(f"No vpc_info.json found at {vpc_info_path}")

if not vpc_id:
    print("vpc_id not found in vpc_info.json. Exiting.")
    sys.exit(1)

# Create IAM role for Flow Logs
role_name = "LabRole"
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

"""try:
    #role = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=str(trust_policy))
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSVPCFlowLogsPushToCloudWatchLogs'
    )
    print("Flow Logs role created")
except iam.exceptions.EntityAlreadyExistsException:
    print("Role already exists")
"""
# Wait 10s for role propagation
import time; time.sleep(15)

# Enable Flow Logs - only REJECT traffic to S3 bucket
ec2.create_flow_logs(
    ResourceType='VPC',
    ResourceIds=[vpc_id],
    TrafficType='REJECT',
    LogDestinationType='s3',
    LogDestination='arn:aws:s3:::polystudents3-lab-4/flowlogs/',
    
)

print("VPC Flow Logs enabled (REJECT only S3)")