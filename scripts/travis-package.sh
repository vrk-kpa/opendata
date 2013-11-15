#! /bin/sh

sshpass -e scp script/install.sh $USERNAME@$SSHHOST:/home/$USERNAME/

exit 0
