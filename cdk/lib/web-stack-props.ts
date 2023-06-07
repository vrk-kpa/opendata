import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';

import { EcsStackProps, EcsStackPropsTaskDef } from './ecs-stack-props';

export interface WebStackProps extends EcsStackProps {
  certificate: acm.ICertificate;
  loadBalancer: elb.ApplicationLoadBalancer;
  nginxTaskDef: EcsStackPropsTaskDef,
  drupalService: ecs.FargateService;
  ckanService: ecs.FargateService;
  allowRobots: string
}
