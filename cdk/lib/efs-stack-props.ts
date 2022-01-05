import * as ec2 from 'aws-cdk-lib/aws-ec2';

import { CommonStackProps } from './common-stack-props';

export interface EfsStackProps extends CommonStackProps {
  vpc: ec2.IVpc;
  importMigrationFs: boolean;
}