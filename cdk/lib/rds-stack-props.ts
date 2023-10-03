import * as ec2 from 'aws-cdk-lib/aws-ec2';

import { CommonStackProps } from './common-stack-props';
import {aws_backup} from "aws-cdk-lib";

export interface RdsStackProps extends CommonStackProps {
  backupPlan: aws_backup.BackupPlan;
  backups: boolean;
  vpc: ec2.IVpc;
  multiAz: boolean;
}
