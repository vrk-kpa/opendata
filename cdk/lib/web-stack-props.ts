import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';

import { EcsStackProps, EcsStackPropsTaskDef } from './ecs-stack-props';

export interface WebStackProps extends EcsStackProps {
  loadBalancerCert?: acm.ICertificate;
  loadBalancer?: elb.IApplicationLoadBalancer;
  nginxTaskDef: EcsStackPropsTaskDef,
  drupalService: ecs.FargateService;
  ckanService: ecs.FargateService;
}