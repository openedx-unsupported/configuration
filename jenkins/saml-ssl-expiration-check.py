import argparse
import logging
import OpenSSL
from datetime import datetime, timedelta
import sys
import yaml
from os.path import basename

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--region', default='us-east-1', required=True,
                        help="AWS Region")

    parser.add_argument('-d', '--days', type=int,
                        help="Alert if SSL certificate will expire within these days", default=90)
    parser.add_argument('-i','--file',
                        help="input YAML file to parse and get SAML cert")
    

    args = parser.parse_args()

    time_now = datetime.now()
    ssl_expire_check = time_now + timedelta(days=args.days)
    saml_cert_file = args.file
    expired_ssl =  basename(saml_cert_file).strip('.yml')

    with open(saml_cert_file) as f:
        secure_config = yaml.safe_load(f)
    cert = secure_config['EDXAPP_SOCIAL_AUTH_SAML_SP_PUBLIC_CERT']
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    cert_expire_date = datetime.strptime(x509.get_notAfter().decode('utf-8'), "%Y%m%d%H%M%S%fZ").date()

    if ssl_expire_check.date() > cert_expire_date:
        logger.info("{} SAML certificate will be expired on  {}".format(expired_ssl,cert_expire_date))
        sys.exit(1)
