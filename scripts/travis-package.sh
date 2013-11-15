#! /bin/sh

echo "## upload ##"
echo "Host $SSHHOST" >> ~/.ssh/config
echo "  StrictHostKeyChecking no" >> ~/.ssh/config
sshpass -e scp scripts/install.sh $USERNAME@$SSHHOST:/home/$USERNAME/ > /dev/null 2>&1

exit 0
