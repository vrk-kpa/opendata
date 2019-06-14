#!/usr/bin/env bash
unset  AWS_SESSION_TOKEN
set -Eeuo pipefail
export AWS_DEFAULT_REGION=eu-west-1

temp_buildtest_role=$(aws sts assume-role \
                    --role-arn "arn:aws:iam::${AWS_BUILDTEST_ACCOUNT_ID}:role/InvokeDeploymentRole" \
                    --role-session-name "deploy-assumed-role")

export AWS_ACCESS_KEY_ID=$(echo $temp_buildtest_role | jq .Credentials.AccessKeyId | xargs)
export AWS_SECRET_ACCESS_KEY=$(echo $temp_buildtest_role | jq .Credentials.SecretAccessKey | xargs)
export AWS_SESSION_TOKEN=$(echo $temp_buildtest_role | jq .Credentials.SessionToken | xargs)

temp_deploy_role=$(aws sts assume-role \
                    --role-arn "arn:aws:iam::${AWS_BUILDTEST_ACCOUNT_ID}:role/DeploymentRole" \
                    --role-session-name "deploy-assumed-role")

export AWS_ACCESS_KEY_ID=$(echo $temp_deploy_role | jq .Credentials.AccessKeyId | xargs)
export AWS_SECRET_ACCESS_KEY=$(echo $temp_deploy_role | jq .Credentials.SecretAccessKey | xargs)
export AWS_SESSION_TOKEN=$(echo $temp_deploy_role | jq .Credentials.SessionToken | xargs)
