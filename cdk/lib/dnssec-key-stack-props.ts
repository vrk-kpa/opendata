import {StackProps} from "aws-cdk-lib";
export interface DnssecKeyStackProps extends StackProps {
  keyAlias: string;
}

