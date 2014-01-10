#! /bin/sh

echo "pwd:"
ls -lah

echo "python:"
python -c "import sys; print sys.path"

echo "path:"
echo $PATH

DATE=`date +%Y-%m-%d_%H_%M_%S`

echo "## upload ##"
echo "Host $SSHHOST" >> ~/.ssh/config
echo "  StrictHostKeyChecking no" >> ~/.ssh/config

echo "[webservers]" > inventory-alpha
echo "$SSHHOST" >> inventory-alpha
echo $PASS | gpg --batch --passphrase-fd 0 --output=vars/private/variables.yml vars/private/variables-alpha.yml.gpg > /dev/null 2>&1
sshpass -e ansible-playbook --inventory-file=inventory-alpha site.yml --user=deploy --ask-pass --extra-vars='accelerate=false' > ansible.output 2>&1
sshpass -e scp ansible.output "$USERNAME@$SSHHOST:/home/$USERNAME/ansible_$DATE.output" > /dev/null 2>&1
rm ansible.output
rm vars/private/variables.yml

exit 0
