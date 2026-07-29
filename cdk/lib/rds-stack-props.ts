import * as ec2 from 'aws-cdk-lib/aws-ec2';

import {aws_backup} from "aws-cdk-lib";
import {EnvStackProps} from "./env-stack-props";

export interface RdsStackProps extends EnvStackProps {
  backupPlan: aws_backup.BackupPlan;
  backups: boolean;
  vpc: ec2.IVpc;
  multiAz: boolean;
}
