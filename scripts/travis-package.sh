#! /bin/sh

echo "## upload ##"
echo "Host $SSHHOST" >> ~/.ssh/config
echo "  StrictHostKeyChecking no" >> ~/.ssh/config

echo "[webservers]" > inventory-alpha
echo "$SSHHOST" >> inventory-alpha
echo $PASS | gpg --batch --passphrase-fd 0 --output=vars/private/variables.yml vars/private/variables-alpha.yml.gpg > /dev/null 2>&1
echo "$DATE" > ansible.output 

for tag in ansible firewall users common resources database nginx ckan drupal; do 
    echo "## $tag ##"
    sshpass -e ansible-playbook --inventory-file=inventory-alpha --user=deploy --ask-pass --extra-vars='accelerate=false' --tags=$tag site.yml >> ansible.output 2>&1
    EXIT_STATUS=$?
    if [ "$EXIT_STATUS" != "0" ]; then
        echo "$tag failed"
        exit $EXIT_STATUS
    fi
done

sshpass -e scp ansible.output "$USERNAME@$SSHHOST:/home/$USERNAME/ansible_$DATE.output" > /dev/null 2>&1
rm ansible.output
rm vars/private/variables.yml

exit $EXIT_STATUS
