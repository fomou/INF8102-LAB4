#!/usr/bin/env python3
import boto3

s3 = boto3.client('s3')
bucket_name = "polystudents3-lab-4"

# Create bucket
s3.create_bucket(Bucket=bucket_name, ACL='private')

# Enable versioning
s3.put_bucket_versioning(
    Bucket=bucket_name,
    VersioningConfiguration={'Status': 'Enabled'}
)

# Block public access
s3.put_public_access_block(
    Bucket=bucket_name,
    PublicAccessBlockConfiguration={
        'BlockPublicAcls': True,
        'IgnorePublicAcls': True,
        'BlockPublicPolicy': True,
        'RestrictPublicBuckets': True
    }
)

# Server-side encryption with your KMS key
s3.put_bucket_encryption(
    Bucket=bucket_name,
    ServerSideEncryptionConfiguration={
        'Rules': [{
            'ApplyServerSideEncryptionByDefault': {
                'SSEAlgorithm': 'aws:kms',
                'KMSMasterKeyID': 'arn:aws:kms:us-east-1:533267435458:key/14b71fda-d863-4406-8e82-b1f77a9d0163'
            }
        }]
    }
)

print(f"S3 bucket {bucket_name} created and secured!")

