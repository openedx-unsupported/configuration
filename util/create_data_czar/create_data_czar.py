import boto3
import argparse
import gnupg
import sys

# Assumes you have GPG already installed
# Assumes that the Data Czars already have your public key
# Asumes that .boto is configured with edX Prod account

# Parser
parser = argparse.ArgumentParser(description="Username of Data Czar.")
parser.add_argument('-u', '--user', help='Email of Data Czar', required=True)
parser.add_argument('-f', '--file', help='Public Key file', required=True)
parser.add_argument('--credentials-only', help='Only create new credentials', default=False, action='store_true')
parser.add_argument('-o', '--orgs', nargs='*', help='Name of the org(s) as list, User need to be a member', default=None)
parser.add_argument('-c', '--creator', help='Name of the creator', default=None)
args = parser.parse_args()

# Import Data Czar GPG Key
gpg = gnupg.GPG()
key_data = open(args.file).read()
import_result = gpg.import_keys(key_data)

# Connect to AWS and create account
iam = boto3.client('iam')

if not args.credentials_only:
    user_response = iam.create_user(UserName=args.user)
    if args.creator:
        tag_response = iam.tag_user(UserName=args.user, Tags=[{'Key': 'Creator', 'Value': args.creator}])

key_response = iam.create_access_key(UserName=args.user)

# Add user to group edx-s3bucket-course-data-readonly
iam.add_user_to_group(GroupName='edx-s3bucket-course-data-readonly', UserName=args.user)

# Add user to it's respective Org
if args.orgs:
    for org in args.orgs:
        user_org = 'edx-course-data-' + org.lower()
        iam.add_user_to_group(GroupName=user_org, UserName=args.user)

# Create AWS Cred String
key = key_response['AccessKey']
credstring = str(f'AWS_ACCESS_KEY_ID = {key["AccessKeyId"]} \nAWS_SECRET_ACCESS_KEY = {key["SecretAccessKey"]}')

# Encrypt file
encrypted_data = gpg.encrypt(credstring, args.user, always_trust=True)
encrypted_string = str(encrypted_data)
gpgfile = open(args.user + '-credentials.txt.gpg', 'w+')
gpgfile.write(encrypted_string)

print('ok: ', encrypted_data.ok)
print('status: ', encrypted_data.status)
print('stderr: ', encrypted_data.stderr)

if encrypted_data.stderr:
    sys.exit(1)
