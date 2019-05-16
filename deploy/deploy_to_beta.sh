#!/bin/bash
set -Eeuo pipefail

ami_id=$(cat "$1")
export AWS_DEFAULT_REGION=eu-west-1

assumed_build_role=$(aws sts assume-role --role-session-name 'deploy-assumed-role' --role-arn arn:aws:iam::"${AWS_BUILDTEST_ACCOUNT_ID}":role/InvokeDeploymentRole)

assumed_build_role_key_id=$(echo "$assumed_build_role" | jq .Credentials.AccessKeyId |xargs)
export AWS_ACCESS_KEY_ID=$assumed_build_role_key_id

assumed_build_role_secret_access_key=$(echo "$assumed_build_role" | jq .Credentials.SecretAccessKey |xargs)
export AWS_SECRET_ACCESS_KEY=$assumed_build_role_secret_access_key

assumed_build_role_session_token=$(echo "$assumed_build_role" | jq .Credentials.SessionToken |xargs)
export AWS_SESSION_TOKEN=$assumed_build_role_session_token

beta_deploy_role=$(aws sts assume-role --role-session-name 'deploy-assumed-role' --role-arn arn:aws:iam::"${AWS_PRODUCTION_ACCOUNT_ID}":role/DeploymentRole)

beta_deploy_role_access_key_id=$(echo "$beta_deploy_role" | jq .Credentials.AccessKeyId |xargs)
export AWS_ACCESS_KEY_ID=$beta_deploy_role_access_key_id

beta_deploy_role_secret_access_key=$(echo "$beta_deploy_role" | jq .Credentials.SecretAccessKey |xargs)
export AWS_SECRET_ACCESS_KEY=$beta_deploy_role_secret_access_key

beta_deploy_role_session_token=$(echo "$beta_deploy_role" | jq .Credentials.SessionToken |xargs)
export AWS_SESSION_TOKEN=$beta_deploy_role_session_token

aws ssm get-parameter --name /beta/web/amiid
aws ssm put-parameter --name /beta/web/amiid --type String --overwrite --allowed-pattern "^ami-[a-z0-9]{17}$" --value "$ami_id"
aws ssm get-parameter --name /beta/web/amiid
