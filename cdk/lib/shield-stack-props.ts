import {aws_cloudfront, aws_elasticloadbalancingv2} from "aws-cdk-lib";
import {CommonStackProps} from "./common-stack-props";

export interface ShieldStackProps extends CommonStackProps{
  loadBalancer: aws_elasticloadbalancingv2.IApplicationLoadBalancer,
  bannedIpsRequestSamplingEnabled: boolean,
  requestSampleAllTrafficEnabled: boolean,
  highPriorityRequestSamplingEnabled: boolean,
  rateLimitRequestSamplingEnabled: boolean
}
