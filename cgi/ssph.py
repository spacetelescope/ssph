#!/internal/data1/other/third_party/envs/pandeia_17/bin/python
import sys
sys.path.append("/internal/data1/other/pylibs/ssph")

import sys
from os import environ
from re import match, compile
import ssph_server.admin as admin
import ssph_server.ssph_auth as auth
import ssph_server.confirm as confirm

from flask import Flask, request, redirect

app = Flask(__name__)


def process_data():
    if request.method == "GET":
        data = request.args
    elif request.method == "POST":
        data = request.form
    return data

@app.route("/secure/ssph_admin.cgi", methods=["GET", "POST"])
def admin_page():
    data = process_data()
    
    return admin.run(data)

@app.route("/secure/ssph_auth.cgi", methods=["GET", "POST"])
def auth_page():
    data = process_data()
    
    return auth.run(data)

@app.route("/unsecured/ssph_confirm.cgi", methods=["GET", "POST"])
def confirm_page():
    data = process_data()
    
    return confirm.run(data)

@app.route("/secure/sso.cgi")
def sso_page():
    shib_vars = compile('(STScI_|Shib_|[a-z_0-9])+')

    msg = 'Content-Type: text/html\n'

    msg += '<!DOCTYPE html><html><body>\n'

    for i in sorted(environ):
        if shib_vars.match(i):
            msg += '<span style="color:red">'
        else:
            msg += '<span>'
    msg += f'<strong>{i}</strong>={environ[i]}</span><br>\n'

    msg += '</body>\n</html>'

    return msg
