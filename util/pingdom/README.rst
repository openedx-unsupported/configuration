Pingdom check creation utility
************

To use:

	.. code-block:: bash

		$ virtualenv -p /usr/bin/python .Python
		$ source .Python/bin/activate
		$ pip install -r requirements.txt

		# Put the export commands in your bashrc or something similar
		$ export PINGDOM_EMAIL=MY_USERNAME
		$ export PINGDOM_PASSWORD=MY_PASSWORD
		$ export PINGDOM_API_KEY=MY_API_KEY

		$ python create_pingdom_alerts.py --alert-config-file ~/my-config-file

There is an [example](example.yml) config file located in this directory. 
        
	
