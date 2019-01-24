# admin_text.py - separates the html from the rest of the admin program
html_page = """
<html>
<head>
<title>Admin SSPH</title>
</head>
<body>

<h1>Admin SSPH</h1>
<a href="/secure/ssph_admin.cgi" target=_blank>dup window</a><br>

<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->
<hr>
<a href="/secure/ssph_admin.cgi?listsp=y">List SP</a>

<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->
<hr>
<a href="/secure/ssph_admin.cgi?listau=y">List Auths</a>

<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->
<hr>

<form action='/secure/ssph_admin.cgi' method=post>
<table>
<tr>
<td> sp             </td> <td> <input type=text name=sp             > </td> <td> Service Provider name  </td>
</tr><tr>
<td> url            </td> <td> <input type=text name=url            > </td> <td> URL to get back to SP  </td>
</tr><tr>
<td> dbtype         </td> <td> <input type=text name=dbtype         > </td> <td> ssph, pymssql, mysqldb, psycopg2 </td>
</tr><tr>
<td valign=top> dbcreds </td> <td> <textarea rows=10 cols=40 name=dbcreds></textarea> </td> <td valign=top> json of credentials    </td>
</tr><tr>
<td> contact        </td> <td> <input type=text name=contact        > </td> <td> name of SP contacts    </td>
</tr><tr>
<td> email          </td> <td> <input type=text name=email          > </td> <td> email of SP contacts   </td>
</tr><tr>
<td> secret         </td> <td> <input type=text name=secret         > </td> <td> SP shared secret       </td>
</tr><tr>
<td> hash           </td> <td> <input type=text name=hash           > </td> <td> md5, sha1, sha224, sha256, sha384, sha512 </td>
</tr>
</table>
<input type=submit>
</form>

<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->
<hr>
<form action='/secure/ssph_admin.cgi' method=post>
<input type=submit name=submit value="Set Database Password">
<input type=text name=db_pass size=80>
</form>

<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->
<hr>
<form action='/secure/ssph_admin.cgi' method=post>
<input type=submit name=get_db_pass value="Get Database Password">
</form>

<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->
<hr>
<form action='/secure/ssph_admin.cgi' method=post>
<input type=text name=delete_sp>
<input type=submit name=delete value="Delete SP">
</form>

<!-- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx -->


</body>
</html>
"""
