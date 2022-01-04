import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';
import * as elb from '@aws-cdk/aws-elasticloadbalancingv2';
import * as efs from '@aws-cdk/aws-efs';
import * as ecr from '@aws-cdk/aws-ecr';
import * as rds from '@aws-cdk/aws-rds';
import * as ec from '@aws-cdk/aws-elasticache';
import * as acm from '@aws-cdk/aws-certificatemanager';

import { EcsStackProps, EcsStackPropsTaskDef } from './ecs-stack-props';

export interface WebStackProps extends EcsStackProps {
  loadBalancerCert?: acm.ICertificate;
  loadBalancer?: elb.IApplicationLoadBalancer;
  nginxTaskDef: EcsStackPropsTaskDef,
  drupalService: ecs.FargateService;
  ckanService: ecs.FargateService;
}