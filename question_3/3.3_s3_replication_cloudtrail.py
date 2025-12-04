import boto3
import json

BUCKET_NAME = "polystudents3-lab-4"
TRAIL_NAME = "tp4-s3-trail"
REGION = "us-east-1"   

session = boto3.Session()
sts = session.client("sts")
account_id = sts.get_caller_identity()["Account"]

s3 = session.client("s3")
cloudtrail = session.client("cloudtrail", region_name=REGION)

# ---------------------------------------------------------------------
# 3.3.1. Build the required CloudTrail bucket policy
# ---------------------------------------------------------------------

bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AWSCloudTrailAclCheck",
            "Effect": "Allow",
            "Principal": {"Service": "cloudtrail.amazonaws.com"},
            "Action": "s3:GetBucketAcl",
            "Resource": f"arn:aws:s3:::{BUCKET_NAME}"
        },
        {
            "Sid": "AWSCloudTrailWrite",
            "Effect": "Allow",
            "Principal": {"Service": "cloudtrail.amazonaws.com"},
            "Action": "s3:PutObject",
            "Resource": f"arn:aws:s3:::{BUCKET_NAME}/AWSLogs/{account_id}/*",
            "Condition": {
                "StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}
            }
        }
    ]
}

# ---------------------------------------------------------------------
# 3.3.2. Attach the policy to the S3 bucket
# ---------------------------------------------------------------------

policy_json = json.dumps(bucket_policy)

print("Updating S3 bucket policy...")
s3.put_bucket_policy(
    Bucket=BUCKET_NAME,
    Policy=policy_json
)

print("Bucket policy updated successfully")

# ---------------------------------------------------------------------
# 3. Create CloudTrail trail
# ---------------------------------------------------------------------

print("Creating CloudTrail trail...")

cloudtrail.create_trail(
    Name=TRAIL_NAME,
    S3BucketName=BUCKET_NAME,
    IncludeGlobalServiceEvents=True,
    IsMultiRegionTrail=True
)

print("[+] CloudTrail trail created successfully")

# ---------------------------------------------------------------------
# 4. Start logging
# ---------------------------------------------------------------------

cloudtrail.start_logging(Name=TRAIL_NAME)

print("CloudTrail logging started")
print("Setup completed")
