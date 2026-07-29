import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';

import { EcsStackProps, EcsStackPropsTaskDef } from './ecs-stack-props';

export interface WebStackProps extends EcsStackProps {
  listener: elb.ApplicationListener;
  nginxTaskDef: EcsStackPropsTaskDef,
  drupalService: ecs.FargateService;
  ckanService: ecs.FargateService;
  allowRobots: string,
}
