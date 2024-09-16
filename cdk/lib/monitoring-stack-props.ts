import { aws_sns as sns } from 'aws-cdk-lib';
import {EnvStackProps} from "./env-stack-props";

export interface MonitoringStackProps extends EnvStackProps {
  sendToZulipTopic: sns.Topic
}

