####
# EDIT THIS FILE TO CONFIGURE YOUR DATABASE

# For the server, open a database here.  Take note that the Pandokia
# database driver does not actually connect to the database until the
# first time you try to use it.
#
# You have to create the tables manually from the schema in schema_core.sql
# You have to set the database password through /secure/ssph_admin.cgi
#

import os.path

#####
# database password - common to all

# The database password is stored in a separate file that belongs
# to the apache user.  Here is the name of the file.

password_file = "/data1/home/sienkiew/work/ssph/testdb/password"

try :
    password = open( password_file, "r").readline().strip()
except IOError :
    password = None

#####
# database: sqlite

if 1 :
    import pandokia.db_sqlite as d
    # sqlite only needs a file, but it needs read/write on the file and
    # the directory it is in.  sqlite is not very good at handling lots
    # of concurrent transactions.
    core_db = d.PandokiaDB("/data1/home/sienkiew/work/ssph/testdb/x.db")

#####
# database: postgres

if 0 :
    import pandokia.db_psycopg2 as d
    core_db = d.PandokiaDB( { 
        'host'      : 'banana.stsci.edu',
        'port'      : 5432,
        'database'  : 'ssph',
        'user'      : 'ssph',
        'password'  : password,
        }
        )

#####
# database: mysql

if 0 :
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

#####
# database: microsoft sql server

if 0 :
    # set environ before the import -- oops, too late!
    # os.environ['TDSVER'] = '8.0'
    import pandokia.db_pymssql as d
    core_db = d.PandokiaDB( {
            'user'          : 'jwstetc_user',
            'server'        : 'ppsdevdb1',
            'port'          : 1433,
            'password'      : password,
            'database'      : 'jwst_sienkiew',
            # 'timeout'       : 0,
            # 'login_timeout' : 0,
            # 'appname'       : ???
            # 'conn_properties': ???
        
        }
        )

