import { NodejsFunction } from 'aws-cdk-lib/aws-lambda-nodejs';
import { CommonStackProps } from './common-stack-props';

export interface MonitoringStackProps extends CommonStackProps {
  sendToZulipLambda: NodejsFunction
}

