#!/bin/bash

read -p "Enter AWS Vault profile name: " prf
read -p "Enter AWS environment name: " env

while :
do
    read -p "Enter key: " key
    read -p "Enter val: " val
    path="/$env/opendata/$key"

    aws-vault exec "$prf" -- aws ssm put-parameter --name "$path" --type "String" --value "$val" --overwrite

    echo "Set parameter $path to $val"
done
