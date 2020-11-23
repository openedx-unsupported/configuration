"""
Set of custom values user for Big Data University deployments
"""
import os
import json

from .production import *
from path import Path as path

CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))

#### BDU config files ##########################################################

with open(CONFIG_ROOT / "bdu.env.json") as env_file:
    BDU_ENV_TOKENS = json.load(env_file)

with open(CONFIG_ROOT / "bdu.auth.json") as env_file:
    BDU_AUTH_TOKENS = json.load(env_file)

### BDU Labs ##################################################################
BDU_LABS_ROOT_URL = BDU_ENV_TOKENS.get('BDU_LABS_ROOT_URL')
BDU_LABS_OAUTH_CLIENT_NAME = BDU_ENV_TOKENS.get('BDU_LABS_OAUTH_CLIENT_NAME')

# BDU Labs API
BDU_LABS_API_URL = BDU_ENV_TOKENS.get('BDU_LABS_API_URL')
BDU_LABS_ACCESS_KEY = BDU_AUTH_TOKENS.get('BDU_LABS_ACCESS_KEY')
BDU_LABS_SECRET_KEY = BDU_AUTH_TOKENS.get('BDU_LABS_SECRET_KEY')


##### ORA2 ######
# Prefix for uploads of example-based assessment AI classifiers
# This can be used to separate uploads for different environments
# within the same S3 bucket.
ORA2_FILEUPLOAD_BACKEND = BDU_ENV_TOKENS.get("ORA2_FILEUPLOAD_BACKEND", 'django')

LOGOUT_REDIRECT_URL = '/'
