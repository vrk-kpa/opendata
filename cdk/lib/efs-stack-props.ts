import * as ec2 from 'aws-cdk-lib/aws-ec2';

import {aws_backup} from "aws-cdk-lib";
import {EnvStackProps} from "./env-stack-props";

export interface EfsStackProps extends EnvStackProps {
  backupPlan: aws_backup.BackupPlan;
  vpc: ec2.IVpc;
  backups: boolean;
}
