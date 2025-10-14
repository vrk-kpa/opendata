import {aws_ssm, CfnParameter, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";

import {EnvStackProps} from "./env-stack-props";

export class ShieldParameterStack extends Stack {
  readonly bannedIpListParameterName: string;
  readonly whitelistedIpListParameterName: string;
  readonly highPriorityCountryCodeListParameterName: string;
  readonly highPriorityRateLimitParameterName: string;
  readonly rateLimitParameterName: string;
  readonly managedRulesParameterName: string;
  readonly wafAutomationArnParameterName: string;
  readonly snsTopicArnParameterName: string;
  readonly evaluationPeriodParameterName: string;
  readonly blockedUserAgentsParameterName: string;

  constructor(scope: Construct, id: string, props: EnvStackProps ) {
    super(scope, id, props);

    this.bannedIpListParameterName = `/${props.environment}/waf/banned_ips`
    new aws_ssm.StringListParameter(this, 'bannedIplist', {
      stringListValue: ["127.0.0.1"],
      description: 'List of banned IP addresses',
      parameterName: this.bannedIpListParameterName
    })

    this.whitelistedIpListParameterName = `/${props.environment}/waf/whitelisted_ips`
    new aws_ssm.StringListParameter(this, 'whitelistedIplist', {
      stringListValue: ["127.0.0.1"],
      description: 'List of whitelisted IP addresses',
      parameterName: this.whitelistedIpListParameterName
    })

    this.highPriorityCountryCodeListParameterName = `/${props.environment}/waf/high_priority_country_codes`
    new aws_ssm.StringListParameter(this, 'highPriorityCountryCodeList', {
      stringListValue: ["Some bogus country code"],
      description: 'Country codes deemed high priority',
      parameterName: this.highPriorityCountryCodeListParameterName
    })

    this.highPriorityRateLimitParameterName = `/${props.environment}/waf/high_priority_rate_limit`
    new aws_ssm.StringParameter(this, 'highPriorityRateLimit', {
      stringValue: '0',
      description: 'Rate limit for high priority country codes',
      parameterName: this.highPriorityRateLimitParameterName
    })

    this.rateLimitParameterName = `/${props.environment}/waf/rate_limit`
    new aws_ssm.StringParameter(this, 'rateLimit', {
      stringValue: '0',
      description: 'Rate limit for others',
      parameterName: this.rateLimitParameterName
    })

    this.managedRulesParameterName = `/${props.environment}/waf/managed_rules`
    new aws_ssm.StringParameter(this, 'managedRules', {
      stringValue: 'some placeholder',
      description: 'JSON value for managed rules',
      parameterName: this.managedRulesParameterName
    })

    this.wafAutomationArnParameterName =`/${props.environment}/waf/waf_automation_arn`
    new aws_ssm.StringParameter(this, 'wafAutomationArn', {
      stringValue: 'some placeholder',
      description: 'Arn of waf automation lambda',
      parameterName: this.wafAutomationArnParameterName,
    })

    this.snsTopicArnParameterName =`/${props.environment}/waf/sns_topic_arn`
    new aws_ssm.StringParameter(this, 'snsTopicArn', {
      stringValue: 'some placeholder',
      description: 'Arn of sns topic',
      parameterName: this.snsTopicArnParameterName,
    })

    this.evaluationPeriodParameterName =`/${props.environment}/waf/evaluation_period`
    new aws_ssm.StringParameter(this, 'evaluationPeriod', {
      stringValue: '0',
      description: 'Evaluation period for rate limits',
      parameterName: this.evaluationPeriodParameterName
    })

    this.blockedUserAgentsParameterName = `/${props.environment}/waf/blocked_user_agents`
    new aws_ssm.StringParameter(this, 'blockedUserAgents', {
      stringValue: "Some bogus user agent",
      description: 'User Agents to be blocked in JSON',
      parameterName: this.blockedUserAgentsParameterName
    })
  }
}
