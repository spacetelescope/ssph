import os
import json
import pandokia.helpers.web as web
import hashlib

default_url = 'https://ssph.stsci.edu/unsecured/ssph_confirm.cgi'
default_url = 'https://etcbrady.stsci.edu/unsecured/ssph_confirm.cgi'

class HashException(Exception):
    '''This happens when the ssph server replies with data that
    is not properly signed.  Either you made a mistake configuring
    your Service Provider into SSPH, or you are *not* talking to
    the SSPH server.
    '''
    pass

class Refused(Exception):
    '''This happens when the ssph server replies with a barf message'''

def ssph_validate(sp, evid, secret, hashclass=hashlib.sha512, url=default_url):

    args = {
        "sp": sp,
        "evid": evid,
        }

    m = hashclass()
    m.update(sp)
    m.update(' ')
    m.update(evid)
    m.update(' ')
    m.update(secret)

    args["sig"] = m.hexdigest()

    print("USING URL",url, args)
    f = web.GET(url, args)
    hash = f.readline().strip()
    info = f.read().strip()
    m = hashclass()
    m.update(info)
    m.update(' ')
    m.update(secret)
    if hash != m.hexdigest() 
        if hash.strip() == 'barf':
            print(hash)
            print(info)
            raise Refused()
        raise HashException('SSPH communication replied with incorrect hash - possible security attack underway')

    return json.loads(info)

if __name__ == '__main__':

    # set this to describe an SP
    sp = 'jwstetc.banana:4460'
    hashclass = hashlib.md5
    secret = 'foobar'

    # set this to a cookie that has an auth in the db
    #cookie1 = '56.1401464172.0'
    cookie1= '2.1401486864.0'

    # set this to a cookie that does not have an auth in the db
    cookie2 = '1231242141224'

    if True:
        # works, replies with a valid response
        print(ssph_validate(sp, cookie1, hashclass = hashclass, secret=secret))
        print()

    if False:
        # cookie not know, barfs
        print(ssph_validate(sp=sp, cookie=cookie2, hashclass=hashclass, secret=secret))
        print()

    if False:
        # signed with wrong secret, barfs
        print(ssph_validate(sp=sp, cookie=cookie1, hashclass=hashclass, secret=secret+"xx"))
        print()
