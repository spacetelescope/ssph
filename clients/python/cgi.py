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
    if 1 :
        print ssph_validate( 
            sp='jwstetc.banana:4460',
            cookie='52.1401226168.0',
            )
        print ""

    if 0 :
        print ssph_validate( 
            sp='jwstetc.banana:4460',
            cookie='52.1401226168.1',
            )
        print ""

    if 0 :
        print ssph_validate(
            sp='jwstetc.banana:4460',
            cookie='52.1401226168.0',
            secret='wrong one'
            )
        print ""

