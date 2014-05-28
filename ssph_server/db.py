# For the server, open a database here.  Take note that the Pandokia
# database driver does not actually connect to the database until the
# first time you try to use it.

import os.path

password = open( os.path.dirname(__file__) + "/password", "r").readline().strip()

# sqlite
if 0 :
    import pandokia.db_sqlite as d
    # sqlite only needs a file, but it needs read/write on the file and
    # the directory it is in.  sqlite is not very good at handling lots
    # of concurrent transactions.
    core_db = d.PandokiaDB("/data1/home/sienkiew/work/ssph/testdb/x.db")

# postgres
if 0 :
    import pandokia.db_psycopg2 as d
    core_db = d.PandokiaDB( { 'database' : 'ssph' } )

# mysql
if 1 :
    import pandokia.db_mysqldb as d
    core_db = d.PandokiaDB( {
            'host'      : 'goldtst',
            'port'      : 23306,
            'user'      : 'pyetc',
            'passwd'    : password,
            'db'        : 'pyetc1',
            'use_unicode' : True,
            }
        )

# microsoft sql server
if 0 :
    import pandokia.db_pymssql as d
    os.environ['TDSVER'] = '8.0'
    core_db = d.PandokiaDB( {
            'user'          : 'jwstetc_user',
            'server'        : 'ppsdevdb',
            'port'          : 1433,
            'password'      : password,
            'database'      : 'jwst_sienkiew',
            # 'timeout'       : 0,
            # 'login_timeout' : 0,
            # 'appname'       : ???
            # 'conn_properties': ???
        
        }
        )
