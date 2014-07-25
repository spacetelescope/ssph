"""
This module implements $DOCUMENTROOT/unsecured/ssph_admin.cgi; it provides
a few management capabilities for SSPH.

Edit the source code to grant permissions.

"""

# put a list of eppn of people who are permitted to create an SP here.
# These people can see and submit this form.
permitted_eppn = (
    'sienkiew@stsci.edu',
    'chanley@stsci.edu',
    'deighton@stsci.edu',
    )

# no edit beyond here
#######


import cgi
import os

html_page = """<html>
<head>
<title>Admin SSPH</title>
</head>
<body>
<h1>Admin SSPH</h1>
<a href="/secure/ssph_admin.cgi" target=_blank>dup window</a><br>
<hr>

<form action='/secure/ssph_admin.cgi' method=post>
<table>
<tr>
<td> sp             </td> <td> <input type=text name=sp             > </td> <td> Service Provider name  </td>
</tr><tr>
<td> url            </td> <td> <input type=text name=url            > </td> <td> URL to get back to SP  </td>
</tr><tr>
<td> confirm_mode   </td> <td> <input type=text name=confirm_mode   > </td> <td> c (cgi) or d (database) </td>
</tr><tr>
<td> dbtype         </td> <td> <input type=text name=dbtype         > </td> <td> ssph, pymssql, mysqldb, psycopg2 </td>
</tr><tr>
<td> dbcreds        </td> <td> <textarea rows=10 cols=40 name=dbcreds>  </textarea> </td> <td> json of credentials    </td>
</tr><tr>
<td> expiry         </td> <td> <input type=text name=expiry         > </td> <td> seconds after login    </td>
</tr><tr>
<td> contact        </td> <td> <input type=text name=contact        > </td> <td> name of SP contacts    </td>
</tr><tr>
<td> email          </td> <td> <input type=text name=email          > </td> <td> email of SP contacts   </td>
</tr><tr>
<td> secret         </td> <td> <input type=text name=secret         > </td> <td> SP shared secret       </td>
</tr><tr>
<td> hash           </td> <td> <input type=text name=hash           > </td> <td> md5, sha1, sha224, sha256, sha384, sha512 >/td>
</tr><tr>
</table>
<input type=submit>
</form>

<hr>
<a href="/secure/ssph_admin.cgi?listsp=y">List SP</a>

<hr>
<a href="/secure/ssph_admin.cgi?listau=y">List Auths</a>

<hr>
<form action='/secure/ssph_admin.cgi' method=post>
<input type=text name=db_pass>
<input type=submit name=submit value="Set Database Password">
</form>

<hr>
<form action='/secure/ssph_admin.cgi' method=post>
<input type=text name=delete_sp>
<input type=submit name=delete value="Delete SP">
</form>


</body>
"""


def run() :

    if not os.environ['eppn'] in permitted_eppn :
        print "status: 500\n\nlogged in but not permitted to admin\n"
        print "your eppn",os.environ['eppn']
        return 1

    # we never get here unless we are authorized IT people, so it is ok
    # to enable tracebacks.  It is easier than providing proper error
    # messages.
    import cgitb
    cgitb.enable()

    # get the cgi parameters
    data = cgi.FieldStorage()

    from ssph_server.validate_sp_ip import validate_ip

    if not validate_ip() :
        print "status: 500\n\nnot permitted\n"
        return 1

    if 'db_pass' in data :
        from ssph_server.db import password_file
        f=open(password_file,"w")
        os.chmod(password_file, 0600)
        f.write(data['db_pass'].value)
        f.close()
        print "content-type: text/plain"
        print ""
        print "done"
        return 0

    if 'sp' in data :
        import json
        from ssph_server.db import core_db

        dbcreds = data['dbcreds'].value

        if dbcreds != "" :
            dbcreds = json.dumps( json.loads( dbcreds ) )

        core_db.execute("""
            INSERT INTO ssph_sp_info 
            ( sp, url, dbtype, dbcreds, expiry, contact, email, confirm_mode, secret, hash )
            VALUES
            ( :1, :2, :3,      :4,      :5,     :6,      :7,    :8,           :9,     :10 )
            """,
            (   data['sp'].value,
                data['url'].value,
                data['dbtype'].value,
                dbcreds,
                data['expiry'].value,
                data['contact'].value,
                data['email'].value,
                data['confirm_mode'].value,
                data['secret'].value,
                data['hash'].value
            )
        )

        core_db.commit()
        print "content-type: text/plain"
        print ""
        print "done"
        return 0 

    if 'delete_sp' in data :
        from ssph_server.db import core_db
        c = core_db.execute("DELETE FROM ssph_sp_info WHERE sp = :1 ",
            ( data['delete_sp'].value, )
            )
        core_db.commit()
        print "content-type: text/plain"
        print ""
        print "done"
        return 0

    if 'listsp' in data :
        t = listtb( 'ssph_sp_info' )
        print "content-type: text/html"
        print ""
        print t.get_html(headings=True)
        return 0

    if 'listau' in data:
        t = listtb( 'ssph_auths' )
        print "content-type: text/html"
        print ""
        print t.get_html(headings=True)
        return 0

    # this is not a form submission
    print "content-type: text/html"
    print ""
    print html_page
    return 0

def listtb( table ):
    import pandokia.text_table
    from ssph_server.db import core_db
    c = core_db.execute("select * from %s" % table)
    t = pandokia.text_table.text_table()
    t.set_html_table_attributes("border=1")
    for col, name in enumerate(c.description) :
        t.define_column( name, col, html=name[0] )
    for row, x in enumerate(c) :
        for col, value in enumerate(x) :
            t.set_value(row, col, value )
    return t

if __name__ == '__main__' :
    t = listsp()
    print t.get_rst()

