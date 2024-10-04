import sys
from os import environ
from re import match, compile
sys.path.append("/Users/riedel/pandeia_b/src/ssph")

from django.http import HttpResponse

import ssph_server.admin as admin
import ssph_server.ssph_auth as auth
import ssph_server.confirm as confirm


def index(request):
    return HttpResponse("no direct access to this server\n(3)")

def admin_page(request):
    response = admin.run(request)
    return response

def auth_page(request):
    response = auth.run(request)
    return response

def confirm_page(request):
    response = confirm.run(request)
    return response

def sso_page(request):
    shib_vars = compile('(STScI_|Shib_|[a-z_0-9])+')

    msg = '<!DOCTYPE html><html><body>\n'

    for i in sorted(environ):
        if shib_vars.match(i):
            msg += '<span style="color:red">'
        else:
            msg += '<span>'
    msg += f'<strong>{i}</strong>={environ[i]}</span><br>\n'

    msg += '</body>\n</html>'

    return HttpResponse(msg)

# Create your views here.
