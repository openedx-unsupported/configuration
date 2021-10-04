import sys
import gnupg
gpg = gnupg.GPG()
key_data = open('CDDTEP_0x2A797C12_public.asc').read()
import_result = gpg.import_keys(key_data)
e = gpg.encrypt('test' , recipients="cddtep@rudn.ru", always_trust=True)
if 'error' in  e.stderr:
  print(e.stderr)
  sys.exit(1)
#print('ok: ', e.ok)
#print('status: ', e.status)
#print('stderr: ', e.stderr)
