import * as ec2 from 'aws-cdk-lib/aws-ec2';

import {EnvStackProps} from "./env-stack-props";

export interface EcStackProps extends EnvStackProps {
  vpc: ec2.IVpc;
  cacheNodeType: string;
  cacheEngineVersion: string;
  cacheNumNodes: number;
}
