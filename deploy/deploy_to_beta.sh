#!/bin/bash
set -Eeuxo pipefail

export AWS_DEFAULT_REGION=eu-west-1
assumed_build_role=$(aws sts assume-role --role-session-name 'deploy-assumed-role' --role-arn arn:aws:iam::${AWS_BUILDTEST_ACCOUNT_ID}:role/InvokeDeploymentRole)
export AWS_ACCESS_KEY_ID=$(echo $assumed_build_role | jq .Credentials.AccessKeyId |xargs)
export AWS_SECRET_ACCESS_KEY=$(echo $assumed_build_role | jq .Credentials.SecretAccessKey |xargs)
export AWS_SESSION_TOKEN=$(echo $assumed_build_role | jq .Credentials.SessionToken |xargs)
production_copy_role=$(aws sts assume-role --role-session-name 'deploy-assumed-role' --role-arn arn:aws:iam::${AWS_PRODUCTION_ACCOUNT_ID}:role/DeploymentRole)
export AWS_ACCESS_KEY_ID=$(echo $production_copy_role | jq .Credentials.AccessKeyId |xargs)
export AWS_SECRET_ACCESS_KEY=$(echo $production_copy_role | jq .Credentials.SecretAccessKey |xargs)
export AWS_SESSION_TOKEN=$(echo $production_copy_role | jq .Credentials.SessionToken |xargs)

aws ssm get-parameter --name /beta/web/amiid
aws ssm put-parameter --name /beta/web/amiid --type String --overwrite --allowed-pattern "^ami-[a-z0-9]{17}$" --value "$(cat $1)"
aws ssm get-parameter --name /beta/web/amiid
