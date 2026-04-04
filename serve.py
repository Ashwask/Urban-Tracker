#!/usr/bin/env python3
import os
os.chdir("/Users/ashwinkulkarni/Documents/Urban Tracker")
from http.server import HTTPServer, SimpleHTTPRequestHandler
httpd = HTTPServer(('0.0.0.0', 7842), SimpleHTTPRequestHandler)
httpd.serve_forever()
