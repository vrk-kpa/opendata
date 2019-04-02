#!/bin/bash

assumed_build_role=$(aws sts assume-role --role-session-name 'build-assumed-role' --role-arn arn:aws:iam::${buildtest_account_id}:role/InvokeAmiCopyFunctionRole)
export AWS_ACCESS_KEY_ID=$(echo $assumed_build_role | jq .Credentials.AccessKeyId |xargs)
export AWS_SECRET_ACCESS_KEY=$(echo $assumed_build_role | jq .Credentials.SecretAccessKey |xargs)
export AWS_SESSION_TOKEN=$(echo $assumed_build_role | jq .Credentials.SessionToken |xargs)
production_copy_role=$(aws sts assume-role --role-session-name 'build-assumed-role' --role-arn arn:aws:iam::${production_account_id}:role/CopyAmiLambdaExecutionRole)
export AWS_ACCESS_KEY_ID=$(echo $production_copy_role | jq .Credentials.AccessKeyId |xargs)
export AWS_SECRET_ACCESS_KEY=$(echo $production_copy_role | jq .Credentials.SecretAccessKey |xargs)
export AWS_SESSION_TOKEN=$(echo $production_copy_role | jq .Credentials.SessionToken |xargs)
aws lambda invoke \
  --cli-read-timeout 600 \
  --function-name CopyAmiFunction \
  --log-type Tail \
  --payload "$(cat manifest.json)" \
  outputfile.txt

cat outputfile.txt
