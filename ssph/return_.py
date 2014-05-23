#!
import sys
import cgi
import os
import re
import json

from ssph.db import core_db

def run() :
    data = cgi.FieldStorage()
    sp, cookie = data['sp'].value.split(',',1)
    c = core_db.execute("SELECT url, dbtype, dbcreds FROM sp_info WHERE sp = :1",(sp,))
    ans = c.fetchone()
    if ans is None :
        print "Content-type: text/plain"
        print ""
        print "Do not know your application ",sp
        return 0
    
    url, dbtype, dbcreds = ans

    url = url + "?c=" + cookie

    blob = { }
    shib_vars = re.compile('(STScI_|Shib_|[a-z_0-9])+')
    for x in os.environ :
      if shib_vars.match(x):
        blob[x] = os.environ[x]

    blob = json.dumps( blob )

    if dbtype == "same" :
        cdb = core_db
    else :
        exec "import pandokia.db_%s as cdbm" % dbtype
        dbcreds = json.loads(dbcreds)
        cdb = cdbm.PandokiaDB( dbcreds )

    cdb.execute("""DELETE FROM ssph_auths
            WHERE sp = :1 AND cookie = :2
            """,
            ( sp, cookie )
        )
    cdb.execute("""INSERT INTO ssph_auths ( sp, cookie, blob )
        VALUES ( :1, :2, :3 )""",
        ( sp, cookie, blob )
        )

    cdb.commit()

    print "Status: 303 See Other"
    print "Location:",url
    print ""

