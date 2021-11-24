# Opendata AWS CDK typescript project

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

 * `npm run build`   compile typescript to js
 * `npm run watch`   watch for changes and compile
 * `npm run test`    perform the jest unit tests
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk synth`       emits the synthesized CloudFormation template

## Context variables

To be able to synthesize / deploy the stacks, one must first initialize `cdk.context.json` using target AWS account, if your target account differs from the accounts that are in the version controlled `cdk.context.json` file.

`aws-vault exec AWS_PROFILE_NAME -- cdk synth -c vpcId=AWS_VPC_ID`

* replace `AWS_PROFILE_NAME` with target account profile name
* replace `AWS_VPC_ID` with target vpc id

This will populate your local cdk.context.json file with metadata about the target AWS environment. After this, you can synthesize, diff, deploy, run tests, etc. without providing context variables in the commands.
