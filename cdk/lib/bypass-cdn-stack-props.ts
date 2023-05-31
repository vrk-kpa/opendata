import {aws_route53} from "aws-cdk-lib";
import * as elb from "aws-cdk-lib/aws-elasticloadbalancingv2";
import {CommonStackProps} from "./common-stack-props";

export interface BypassCdnStackProps extends CommonStackProps {
  loadbalancer: elb.IApplicationLoadBalancer
}
