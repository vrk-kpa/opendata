import {CommonStackProps} from "./common-stack-props";

export interface ClusterStackProps extends CommonStackProps {
  vpcId: string
}
