import {EnvStackProps} from "./env-stack-props";
import {EnvProps} from "./env-props";
import { EcsStackPropsTaskDef } from "./ecs-stack-props";
import {ICluster} from 'aws-cdk-lib/aws-ecs';
import { ITopic } from "aws-cdk-lib/aws-sns";

export interface ClamavScannerStackProps extends EnvStackProps {
  envProps: EnvProps;
  cluster: ICluster;
  topic: ITopic;
  clamavTaskDef: EcsStackPropsTaskDef,
}

