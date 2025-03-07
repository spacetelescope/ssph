#!/internal/data1/other/third_party/envs/pandeia_18/bin/python
from os import environ
from re import match, compile

shib_vars = compile('(STScI_|Shib_|[a-z_0-9])+')

print('Content-Type: text/html')
print()

print('<!DOCTYPE html><html><body>')

for i in sorted(environ):
  if shib_vars.match(i):
    print('<span style="color:red">')
  else:
    print('<span>')
  print('<strong>' + i + '</strong>=' + environ[i] + '</span><br>')

print('</body></html>')
