
# Automated deployment using Git, Ansible and CloudFormation

	virtualenv env-aws
	source env-aws/bin/activate
	pip install boto

	cp secrets-example.txt secrets.py
	nano secrets.py
	# Fill in the blanks
	
	# Copy Git-accessible key to working directory with filename set in settings.py
	
	python deploy.py
