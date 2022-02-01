import logging
import sys
import argparse
import boto3.session
import botocore.exceptions

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Assumes that the Data Czars already have your public key
# Asumes that  boto3 is configured with edX Prod account

def delete_iam_user(session: boto3.session.Session, user_name: str) -> None:
    """For a given boto3.session.Session, delete the IAM User and all assoc'd resources."""
    iam = session.resource("iam")
    iam_client = session.client("iam")
    user = iam.User(user_name)
    try:
        user.load()
    except botocore.exceptions.ClientError as client_error:
        # If load failed with NoSuchEntity, IAM User doesn't exist.
        if client_error.response.get("Error", {}).get("Code", "") == "NoSuchEntity":
            logger.error(f"User {user_name} does not exist")
            return
        raise client_error
    logger.debug(f"Deleting IAM User: {user.arn}")
    for group in user.groups.all():
        logger.debug(f"Removing {user.arn} from Group {group.arn}")
        user.remove_group(GroupName=group.name)
    try:
        login_profile = iam.LoginProfile(user.name)
        login_profile.load()
        logger.debug(f"Deleting Login Profile (I.E. Password) from {user.arn}")
        login_profile.delete()
    except botocore.exceptions.ClientError as client_error:
        # If load failed with NoSuchEntity, No Login Profile
        if client_error.response.get("Error", {}).get("Code", "") != "NoSuchEntity":
            raise client_error
    for access_key in user.access_keys.all():
        logger.debug(f"Deleting Access Key from {user.arn}: {access_key.access_key_id}")
        access_key.delete()
    for policy in user.policies.all():
        logger.debug(f"Deleting Inline Policy from {user.arn}: {policy.name}")
        policy.delete()
    for policy in user.attached_policies.all():
        logger.debug(f"Detaching Managed Policy from {user.arn}: {policy.arn}")
        user.detach_policy(PolicyArn=policy.arn)
    # Deleting IAM User
    user.delete()
    logger.info(f"Deleted IAM user: {user.name}")


if __name__ == "__main__":
    # Parser
    parser = argparse.ArgumentParser(description="Username of Data Czar.")
    parser.add_argument('-u', '--user', help='Email of Data Czar', required=True)
    args = parser.parse_args()

    # Create boto3 session and delete user
    user_name = args.user
    session = boto3.session.Session()
    delete_iam_user(session, user_name)
