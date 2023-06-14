import {aws_ec2, aws_rds, StackProps} from "aws-cdk-lib";

export interface CreateDatabasesAndUsersProps extends StackProps{
  datastoreInstance: aws_rds.IDatabaseInstance,
  datastoreCredentials: aws_rds.Credentials,
  vpc: aws_ec2.IVpc;
}
