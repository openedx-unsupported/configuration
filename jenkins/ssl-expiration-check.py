import boto3
import argparse
import logging
import ssl
import OpenSSL
import smtplib
from datetime import date, datetime, timedelta
from socket import socket
from pprint import pformat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_an_email(toaddr, fromaddr, expired_ssl_message, not_check_message, region):
    client = boto3.client('ses', region_name=region)

    message = """

    <p>Hello,</p>

    <p>Certificates that are associated with these load-balancers will be expired in next 30 days: </p>

    <p> {expired_ssl_message} </p>

    <p> These ELBs have SSL certificate but don't have any instance associated to them: </p>

    <p> {not_check_message} </p>

    """.format(expired_ssl_message=expired_ssl_message, not_check_message=not_check_message)
    client.send_email(
        Source=fromaddr,
        Destination={
            'ToAddresses': [
                toaddr
            ]
        },
        Message={
            'Subject': {
                'Data': 'These Certificates will be expired in the next 30 days',
                'Charset': 'utf-8'
            },
            'Body': {
                'Html':{
                    'Data': message,
                    'Charset': 'utf-8'
                }
            }
        }
    )

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Find the SSL Certificates that will expire after X days.")

    parser.add_argument('-e', '--region', default='us-east-1', required=True,
                        help="AWS Region for getting the records", type=str)

    parser.add_argument('-d', '--days', type=int,
                        help="Alert if SSL certificate will expire within these days", default=30)
    
    email_args = parser.add_argument_group("Email Arguments",
                                                "Args for sending email.")

    email_args.add_argument('-r', '--recipient', type=str,
                        help='Recipient email address')

    email_args.add_argument('-f', '--from-email', type=str,
                                 help="Sender email address for email notifications. "
                                      "Email notifications will be disabled if not provided")

    args = parser.parse_args()

    expire_ssl = []
    time_now = datetime.now()
    ssl_expire_check = time_now + timedelta(days=args.days)
    
    elb_conn = boto3.client('elb', region_name=args.region)
    elbs = elb_conn.describe_load_balancers()['LoadBalancerDescriptions']

    elbs_with_ssl = [elb for elb in elbs for listener in elb['ListenerDescriptions'] if (listener['Listener']['LoadBalancerPort'] == 443)]

    elbs_to_check = [(elb['LoadBalancerName'],elb['DNSName']) for elb in elbs_with_ssl if elb['Instances']]

    elbs_not_need_to_check = [elb['DNSName'] for elb in elbs_with_ssl if not elb['Instances']]

    for elb in elbs_to_check:
        elb_tags = elb_conn.describe_tags(LoadBalancerNames=[elb[0]])['TagDescriptions'][0]['Tags']
        for tag in elb_tags:
          if 'kubernetes.io' in tag["Key"]:
              break
        else:
            print("Checking {}".format(elb[1]))
            cert = ssl.get_server_certificate((elb[1], 443))
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
            cert_expire_date = datetime.strptime(x509.get_notAfter().decode(), "%Y%m%d%H%M%S%fZ").date()
            if ssl_expire_check.date() > cert_expire_date:
                print("Expires {}".format(cert_expire_date))
                expire_ssl.append((elb[1],cert_expire_date))

    if expire_ssl or elbs_not_need_to_check:
        expired_ssl_message = pformat(expire_ssl)
        not_check_message = pformat(elbs_not_need_to_check)
        print(not_check_message)
        if args.from_email and args.recipient:
            send_an_email(args.recipient, args.from_email, expired_ssl_message, not_check_message, args.region)
