import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';

import { CommonStackProps } from './common-stack-props';

export interface ElbStackProps extends CommonStackProps {
  vpc: ec2.IVpc;
}