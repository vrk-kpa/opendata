
import {EnvStackProps} from "./env-stack-props";

export interface ClusterStackProps extends EnvStackProps {
  vpcId: string
}
