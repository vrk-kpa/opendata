import {EnvStackProps} from "./env-stack-props";
import {aws_ssm} from "aws-cdk-lib";

export interface ShieldStackProps extends EnvStackProps{
  bannedIpsRequestSamplingEnabled: boolean,
  requestSampleAllTrafficEnabled: boolean,
  highPriorityRequestSamplingEnabled: boolean,
  rateLimitRequestSamplingEnabled: boolean,
  cloudfrontDistributionArn: aws_ssm.IStringParameter,
  bannedIpListParameterName: string,
  whitelistedIpListParameterName: string,
  highPriorityCountryCodeListParameterName: string,
  highPriorityRateLimit: aws_ssm.IStringParameter,
  rateLimit: aws_ssm.IStringParameter,
  managedRulesParameterName: string,
  wafAutomationArn: aws_ssm.IStringParameter,
  snsTopicArn: aws_ssm.IStringParameter
}
