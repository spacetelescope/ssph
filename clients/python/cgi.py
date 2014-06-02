import os
import json

import pandokia.helpers.web as web

class HashException(BaseException) :
    '''This happens when the ssph server replies with data that
    is not properly signed.  Either you made a mistake configuring
    your Service Provider into SSPH, or you are *not* talking to
    the SSPH server.
    '''
    pass

def ssph_validate( sp, cookie, secret=None, hashclass=None, url=None, garbage = None ) :
    if url is None :
        url = "https://etcbrady.stsci.edu/unsecured/ssph_confirm.cgi"
    if hashclass is None :
        import hashlib
        hashclass = hashlib.sha1
    if secret is None :
        secret = "12345678"
    if garbage is None :
        garbage = ''.join( '%02x' % ord(x) for x in os.urandom(10) )

    args = {
        "sp" : sp,
        "cookie" : cookie,
        "garbage" : garbage,
        }

    m = hashclass()
    m.update(garbage)
    m.update(' ')
    m.update( sp )
    m.update(' ')
    m.update( cookie )
    m.update(' ')
    m.update( secret )

    args["sig"] = m.hexdigest()
    
    f = web.GET( url, args )
    hash = f.readline()
    info = f.read().strip()
    m = hashclass()
    m.update( info )
    if hash.strip() != m.hexdigest() :
        if hash.strip() == 'barf' :
            print hash
            print info
        raise HashException('SSPH communication replied with incorrect hash - possible security attack underway')

    return info
    return json.loads(info)

if __name__ == '__main__' :
    import hashlib

    # set this to describe an SP 
    sp = 'jwstetc.banana:4460'
    hashclass = hashlib.md5
    secret = 'foobar'

    # set this to a cookie that has an auth in the db
    cookie1 = '56.1401464172.0'
    cookie1= '2.1401486864.0'

    # set this to a cookie that does not have an auth in the db
    cookie2 = '1231242141224'

    if 1 :
        # works, replies with a valid response
        print ssph_validate( sp=sp, cookie= cookie1, hashclass = hashclass, secret=secret )
        print ""

    if 0 :
        # cookie not know, barfs
        print ssph_validate( sp=sp, cookie= cookie2, hashclass = hashclass, secret=secret )
        print ""

    if 0 :
        # signed with wrong secret, barfs
        print ssph_validate( sp=sp, cookie= cookie1, hashclass = hashclass, secret=secret+"xx" )
        print ""

