import {aws_ec2, aws_rds, StackProps} from "aws-cdk-lib";
import {CommonStackProps} from "./common-stack-props";

export interface LambdaStackProps extends CommonStackProps {
  datastoreInstance: aws_rds.IDatabaseInstance;
  datastoreCredentials: aws_rds.Credentials;
  vpc: aws_ec2.IVpc;
}
