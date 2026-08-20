import ast, sys
f = r'D:\ClawAI\clawai\desktop_server.py'
t = open(f).read()
ast.parse(t)
print('OK')
