import {StackProps} from "aws-cdk-lib";

export interface CiTestStackProps extends StackProps {
  testBucketName: string,
  githubOrg: string,
  githubRepo: string
}
