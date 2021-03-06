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

password_file = '/internal/data1/other/config/pswd'

try:
    password = open(password_file, "r").readline().strip()
except IOError:
    password = None

#####
# database: sqlite
# MOVE THE DATABASE LOCATION BEFORE ACTUAL USE
if False:
    import pandokia.db_sqlite as d
    # sqlite only needs a file, but it needs read/write on the file and
    # the directory it is in.  sqlite is not very good at handling lots
    # of concurrent transactions.
    core_db = d.PandokiaDB("/internal/data1/other/logs/test_db.db")

#####
# database: postgres

if False:
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

if True:
    import pandokia.db_mysqldb as d
    core_db = d.PandokiaDB( {
            'host'      : 'plssphdb2',
            'port'      : 3306,
            'user'      : 'etcadmin',
            'passwd'    : password, # stored in /internal/data1/other/config/pswd
            'db'        : 'ssph',
            'use_unicode' : True,
            }
        )

#####
# database: microsoft sql server

if False:
    # set environ before the import -- oops, too late!
    # os.environ['TDSVER'] = '8.0'
    import pandokia.db_pymssql as d
    core_db = d.PandokiaDB( {
            'user'          : 'ssph_server',
            'server'        : 'gatordb',
            'port'          : 1433,
            'password'      : password,
            'database'      : 'ssph',
            # 'timeout'       : 0,
            # 'login_timeout' : 0,
            # 'appname'       : ???
            # 'conn_properties': ???

        }
        )
