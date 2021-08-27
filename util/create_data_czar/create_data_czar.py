import boto
import argparse
import gnupg

# Assumes you have GPG already installed
# Assumes that the Data Czars already have your public key
# Asumes that .boto is configured with edX Prod account

# Parser
parser = argparse.ArgumentParser(description="Username of Data Czar.")
parser.add_argument('-u', '--user', help='Email of Data Czar', required=True)
parser.add_argument('-f', '--file', help='Public Key file', required=True)
parser.add_argument('--credentials-only', help='Only create new credentials', default=False, action='store_true')
parser.add_argument('-o', '--orgs', nargs='*', help='Name of the org(s) as list, User need to be a member', default=None)
args = parser.parse_args()

# Import Data Czar GPG Key
gpg = gnupg.GPG()
key_data = open(args.file).read()
import_result = gpg.import_keys(key_data)

# Connect to AWS and create account
iam = boto.connect_iam()

if not args.credentials_only:
    user_response = iam.create_user(args.user)

key_response = iam.create_access_key(args.user)

# Add user to group edx-s3bucket-course-data-readonly
iam.add_user_to_group('edx-s3bucket-course-data-readonly', args.user)

# Add user to it's respective Org
if args.orgs:
    for org in args.orgs:
        user_org = 'edx-course-data-' + org.lower()
        iam.add_user_to_group(user_org, args.user)

# Create AWS Cred String
key = key_response.create_access_key_response.create_access_key_result.access_key
credstring = str('AWS_ACCESS_KEY_ID = ' + key.access_key_id + '\n' + 'AWS_SECRET_ACCESS_KEY = ' + key.secret_access_key)

# Encrypt file
encrypted_data = gpg.encrypt(credstring, args.user, always_trust=True)
encrypted_string = str(encrypted_data)
gpgfile = open(args.user + '-credentials.txt.gpg', 'w+')
gpgfile.write(encrypted_string)

print('ok: ', encrypted_data.ok)
print('status: ', encrypted_data.status)
print('stderr: ', encrypted_data.stderr)
