import {aws_ec2, aws_rds, StackProps} from "aws-cdk-lib";

import {EnvStackProps} from "./env-stack-props";

export interface LambdaStackProps extends EnvStackProps {
  datastoreInstance: aws_rds.IDatabaseInstance;
  datastoreCredentials: aws_rds.Credentials;
  vpc: aws_ec2.IVpc;
}
