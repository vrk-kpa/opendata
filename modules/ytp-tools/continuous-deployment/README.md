
# Automated deployment using Git, Ansible and CloudFormation

    sudo pip install boto
    sudo pip install ansible
    sudo pip install requests

    cp secrets-example.txt secrets.py
    nano secrets.py
    # Fill in the blanks

    nano ~/.ssh/config
    # Host *.compute.amazonaws.com
    # StrictHostKeyChecking no
    # UserKnownHostsFile=/dev/null
    chmod go-rwx ~/.ssh/config
    
    python deploy.py
