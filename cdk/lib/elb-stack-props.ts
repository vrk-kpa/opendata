import {aws_ec2 as ec2, aws_certificatemanager as acm} from 'aws-cdk-lib';

import { CommonStackProps } from './common-stack-props';

export interface ElbStackProps extends CommonStackProps {
  vpc: ec2.IVpc;
}
