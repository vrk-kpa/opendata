import {EnvStackProps} from "./env-stack-props";
import {aws_ec2, aws_elasticloadbalancingv2, aws_ssm} from "aws-cdk-lib";

export interface ShieldStackProps extends EnvStackProps{
  bannedIpsRequestSamplingEnabled: boolean,
  requestSampleAllTrafficEnabled: boolean,
  highPriorityRequestSamplingEnabled: boolean,
  rateLimitRequestSamplingEnabled: boolean,
  bannedIpListParameterName: string,
  whitelistedIpListParameterName: string,
  highPriorityCountryCodeListParameterName: string,
  highPriorityRateLimitParameterName: string
  rateLimitParameterName: string
  managedRulesParameterName: string,
  wafAutomationArnParameterName: string
  snsTopicArnParameterName: string
  evaluationPeriodParameterName: string,
  loadBalancer: aws_elasticloadbalancingv2.ApplicationLoadBalancer,
  blockedUserAgentsParameterName: string
}
