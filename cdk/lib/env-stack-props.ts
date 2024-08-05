import {StackProps} from "aws-cdk-lib";
import {EnvProps} from "./env-props";

export interface EnvStackProps extends StackProps {
  environment: string;
}
