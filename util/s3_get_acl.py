import csv
from botocore.exceptions import ClientError
import backoff
import click
import boto3


MAX_TRIES = 5

class S3BotoWrapper:
    def __init__(self):
        self.client = boto3.client('s3')

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def get_object_acl(self, bucket_name, obj_key):
        return self.client.get_object_acl(Bucket=bucket_name, Key=obj_key)


def get_object_acl(bucket_name, object_name):
    client = S3BotoWrapper()
    try:
        # Get the ACL for the object
        response = client.get_object_acl(bucket_name, object_name)
        acl = response['Grants']
        return acl
    except Exception as e:
        print(f"Error retrieving ACL for {object_name}: {str(e)}")
        return None


def read_csv_file(file_path):
    output_file = "acl.csv"
    with open(file_path, 'r') as file, open(output_file, 'w', newline='') as output_file:
        reader = csv.reader(file)
        writer = csv.writer(output_file)
        for row in reader:
            print(row)
            bucket_name = row[0]
            object_name = row[1]
            acl = get_object_acl(bucket_name, object_name)
            row.append(acl)  # Append the ACL to the row
            writer.writerow(row)
        # if acl is not None:
        #         print(f"Object: {object_name}, ACL: {acl}")


@click.command()
@click.option('--file_name', required=True, help='Use to identify the file name')
def controller(file_name):
    obj_dict = read_csv_file(file_name)


if __name__ == '__main__':
    controller()
