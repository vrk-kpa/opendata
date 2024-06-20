import {EnvStackProps} from "./env-stack-props";
import {ICluster, ITaskDefinition} from 'aws-cdk-lib/aws-ecs';
import { ITopic } from "aws-cdk-lib/aws-sns";

export interface ClamavScanProps extends EnvStackProps {
  cluster: ICluster;
  task: ITaskDefinition;
  snsTopic: ITopic;
  subnetIds: String[]
}


