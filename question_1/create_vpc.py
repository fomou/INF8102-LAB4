#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
import time
import json
import os
ec2 = boto3.client('ec2')
region = 'us-east-1'
ec2_resource = boto3.resource('ec2', region_name=region)

print("Creating VPC 10.0.0.0/16...")
vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
vpc_id = vpc['Vpc']['VpcId']
ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': 'polystudent-vpc'}])
ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})

# Internet Gateway
print("Creating Internet Gateway...")
igw = ec2.create_internet_gateway()
igw_id = igw['InternetGateway']['InternetGatewayId']
ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

# Get AZs
azs = ['us-east-1a', 'us-east-1b']

# Public Subnets
pub_subnets = []
for i, az in enumerate(azs):
    subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock=f'10.0.{10+i*10}.0/24', AvailabilityZone=az)
    subnet_id = subnet['Subnet']['SubnetId']
    ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': f'public-{az[-1]}'}])
    ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={'Value': True})
    pub_subnets.append(subnet_id)
    print(f"Public subnet created: {subnet_id} in {az}")

# Private Subnets
priv_subnets = []
for i, az in enumerate(azs):
    subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock=f'10.0.{110+i*10}.0/24', AvailabilityZone=az)
    subnet_id = subnet['Subnet']['SubnetId']
    ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': f'private-{az[-1]}'}])
    priv_subnets.append(subnet_id)
    print(f"Private subnet created: {subnet_id} in {az}")

# NAT Gateways (one per AZ)
nat_gateways = []
for i, pub_subnet in enumerate(pub_subnets):
    print(f"Creating EIP and NAT Gateway in {azs[i]}...")
    eip = ec2.allocate_address(Domain='vpc')
    nat = ec2.create_nat_gateway(SubnetId=pub_subnet, AllocationId=eip['AllocationId'])
    nat_id = nat['NatGateway']['NatGatewayId']
    waiter = ec2.get_waiter('nat_gateway_available')
    waiter.wait(NatGatewayIds=[nat_id])
    nat_gateways.append(nat_id)
    print(f"NAT Gateway {nat_id} ready")

# Public Route Table
pub_rt = ec2.create_route_table(VpcId=vpc_id)['RouteTable']
pub_rt_id = pub_rt['RouteTableId']
ec2.create_route(RouteTableId=pub_rt_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
for subnet_id in pub_subnets:
    ec2.associate_route_table(RouteTableId=pub_rt_id, SubnetId=subnet_id)

# Private Route Tables + NAT routes
for i, (priv_subnet, nat_id) in enumerate(zip(priv_subnets, nat_gateways)):
    rt = ec2.create_route_table(VpcId=vpc_id)['RouteTable']
    rt_id = rt['RouteTableId']
    ec2.create_tags(Resources=[rt_id], Tags=[{'Key': 'Name', 'Value': f'private-rt-{azs[i][-1]}'}])
    ec2.create_route(RouteTableId=rt_id, DestinationCidrBlock='0.0.0.0/0', NatGatewayId=nat_id)
    ec2.associate_route_table(RouteTableId=rt_id, SubnetId=priv_subnet)

# Security Group
sg = ec2.create_security_group(
    GroupName='polystudent-sg',
    Description='TP4 - Allow all required ports',
    VpcId=vpc_id
)
sg_id = sg['GroupId']
ec2.authorize_security_group_ingress(
    GroupId=sg_id,
    IpPermissions=[
        {'IpProtocol': 'tcp', 'FromPort': p, 'ToPort': p, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        for p in [22, 80, 443, 53, 1433, 5432, 3306, 3389, 1514]
    ] + [
        {'IpProtocol': 'tcp', 'FromPort': 9200, 'ToPort': 9300, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        {'IpProtocol': 'udp', 'FromPort': 53, 'ToPort': 53, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ]
)

# Save or update JSON file in parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
out_path = os.path.join(parent_dir, "vpc_info.json")

data = {}
if os.path.exists(out_path):
    try:
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        data = {}

data.update({
    "vpc_id": vpc_id,
    "sg_id": sg_id,
    "public_subnets": pub_subnets,
    "private_subnets": priv_subnets
})

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Saved VPC info to {out_path}")

print(f"VPC created successfully!")
print(f"VPC ID: {vpc_id}")
print(f"Security Group: {sg_id}")
print(f"Public Subnets: {pub_subnets}")
print(f"Private Subnets: {priv_subnets}")