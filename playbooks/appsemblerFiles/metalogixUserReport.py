"""
First do the following:

ssh to the Metalogix server

```
(if necessary): sudo mv /tmp/metalogix_users.csv /tmp/metalogix_users.(date).csv
sudo su edxapp -s /bin/bash
cd ~/edx-platform
source ~/edxapp_env
./manage.py lms 6002exportusers.csv --settings=aws_appsembler
```

This will output the file transfer_users.txt.
Then

```
python
```

and paste in this code.
Exit the Metalogix server terminal session, `scp` the file to your local drive
and email to Cathy or other contact at Metalogix.
"""




import json
import csv

fp = open('/tmp/metalogix_users.csv', 'w')
jsonfp = open('transfer_users.txt', 'r')
userjson = jsonfp.read()
users = json.loads(userjson)

writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
writer.writerow(['#user_id', 'Username','full_name','Email domain','Is_active','Last_login','date_joined'])

for user in users:
    user_id = user['up']['user_id']
    username = user['u']['username']
    fullname = user['up']['name']
    emaildomain = user['u']['email'].split('@')[1]
    isactive = user['u']['is_active']
    lastlogin = user['u']['last_login']
    datejoined = user['u']['date_joined']
    output_data = [user_id, username, fullname, emaildomain, isactive, lastlogin, datejoined]
    encoded_row = [unicode(s).encode('utf-8') for s in output_data]
    writer.writerow(encoded_row)

fp.close()