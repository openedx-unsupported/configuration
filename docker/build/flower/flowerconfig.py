
import os

address = os.getenv('ADDRESS', "0.0.0.0")
port = os.getenv('PORT', 5555)

oauth2_key = os.getenv('OAUTH2_KEY', None)
oauth2_secret = os.getenv('OAUTH2_SECRET', None)
oauth2_redirect_uri = os.getenv('OAUTH2_REDIRECT_URI', None)
auth = os.getenv('AUTH', None)
