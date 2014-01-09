#! /bin/sh

DATE=`date +%Y-%m-%d_%H_%M_%S`

echo "## upload ##"
echo "Host $SSHHOST" >> ~/.ssh/config
echo "  StrictHostKeyChecking no" >> ~/.ssh/config

sshpass -e ansible-playbook --inventory-file=inventory-alpha site.yml --user=deploy --ask-pass > ansible.output 2>&1
sshpass -e scp ansible.output "$USERNAME@$SSHHOST:/home/$USERNAME/ansible_$DATE.output" > /dev/null 2>&1
rm ansible.output

exit 0
