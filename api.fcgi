#!/home1/culturp7/public_html/api-dev/v1/api-env/bin/python3

from flup.server.fcgi import WSGIServer
from run import api

WSGIServer(api).run()
