import { NodejsFunction } from 'aws-cdk-lib/aws-lambda-nodejs';
import {EnvStackProps} from "./env-stack-props";

export interface MonitoringStackProps extends EnvStackProps {
  sendToZulipLambda: NodejsFunction
}

