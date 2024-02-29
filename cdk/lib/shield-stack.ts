import {
  aws_lambda,
  aws_shield,
  aws_sns,
  aws_ssm,
  aws_wafv2,
  Stack, Token, CfnParameter, aws_sns_subscriptions, aws_cloudfront
} from "aws-cdk-lib";
import {Construct} from "constructs";

import {ShieldStackProps} from "./shield-stack-props";


export class ShieldStack extends Stack {
  constructor(scope: Construct, id: string, props: ShieldStackProps) {
    super(scope, id, props);

    const cloudfrontDistributionArn = aws_ssm.StringParameter.fromStringParameterName(this,'cloudfrontDistributionArn',
      `/${props.environment}/waf/cloudfrontDistributionArn`)

    const cfnProtection = new aws_shield.CfnProtection(this, 'ShieldProtection', {
      name: 'Cloudfront distribution',
      resourceArn: cloudfrontDistributionArn.stringValue
    })
    

    const banned_ips = new CfnParameter(this, 'bannedIpsList', {
      type: 'AWS::SSM::Parameter::Value<List<String>>',
      default: `/${props.environment}/waf/banned_ips`
    })

    const cfnBannedIPSet = new aws_wafv2.CfnIPSet(this, 'BannedIPSet', {
      name: 'banned-ips',
      scope: 'CLOUDFRONT',
      ipAddressVersion: "IPV4",
      addresses: banned_ips.valueAsList
    })

    const whitelisted_ips = new CfnParameter(this, 'whitelistedIpsList', {
      type: 'AWS::SSM::Parameter::Value<List<String>>',
      default: `/${props.environment}/waf/whitelisted_ips`
    })

    const cfnWhiteListedIpSet = new aws_wafv2.CfnIPSet(this, 'WhitelistedIPSet', {
      name: 'whitelisted-ips',
      scope: 'CLOUDFRONT',
      ipAddressVersion: "IPV4",
      addresses: whitelisted_ips.valueAsList
    })


    const highPriorityCountryCodesParameter = new CfnParameter(this,  'highPriorityCountryCodesParameter', {
      type: 'AWS::SSM::Parameter::Value<List<String>>',
      default: `/${props.environment}/waf/high_priority_country_codes`
    });


    const highPriorityRateLimit = aws_ssm.StringParameter.fromStringParameterName(this, 'highPriorityRateLimit',
      `/${props.environment}/waf/high_priority_rate_limit`);

    const rateLimit = aws_ssm.StringParameter.fromStringParameterName(this, 'rateLimit',
      `/${props.environment}/waf/rate_limit`);


    const managedRulesParameter = aws_ssm.StringParameter.valueFromLookup(this, `/${props.environment}/waf/managed_rules`)

    const managedRules = managedRulesParameter.startsWith("dummy-value") ? "dummy" : JSON.parse(managedRulesParameter)

    let rules = [
      {
        name: "block-banned_ips",
        priority: 0,
        action: {
          block: {
          }
        },
        statement: {
          ipSetReferenceStatement: {
            arn: cfnBannedIPSet.attrArn
          }
        },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "banned-ips",
          sampledRequestsEnabled: props.bannedIpsRequestSamplingEnabled
        },
      },
      {
        name: "allow-whitelisted_ips",
        priority: 1,
        action: {
          allow: {
          }
        },
        statement: {
          ipSetReferenceStatement: {
            arn: cfnWhiteListedIpSet.attrArn
          }
        },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "whitelisted-ips",
          sampledRequestsEnabled: false
        },
      },
      {
        name: "WAFAutomationProtectionRule",
        priority: 2,
        action: {
          count: {
          }
        },
        statement: {
          notStatement: {
            statement: {
              geoMatchStatement: {
                countryCodes: highPriorityCountryCodesParameter.valueAsList
              }
            }
          }
        },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "waf-automation-geoblocked-requests",
          sampledRequestsEnabled: true
        },
      },
      {
        name: "rate-limit-finland",
        priority: 3,
        action: {
          block: {
          }
        },
        statement: {
          rateBasedStatement: {
            limit: Token.asNumber(highPriorityRateLimit.stringValue),
            aggregateKeyType: "IP",
            scopeDownStatement: {
              geoMatchStatement: {
                countryCodes: highPriorityCountryCodesParameter.valueAsList
              }
            }
          }
        },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "request-rate-limit-finland",
          sampledRequestsEnabled: props.highPriorityRequestSamplingEnabled
        },
      },
      {
        name: "rate-limit-world",
        priority: 4,
        action: {
          block: {
          }
        },
        statement: {
          rateBasedStatement: {
            limit: Token.asNumber(rateLimit.stringValue),
            aggregateKeyType: "IP",
            scopeDownStatement: {
              notStatement: {
                statement: {
                  geoMatchStatement: {
                    countryCodes: highPriorityCountryCodesParameter.valueAsList
                  }
                }
              }
            }
          }
        },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "request-rate-limit-world",
          sampledRequestsEnabled: props.rateLimitRequestSamplingEnabled
        },
      },
    ]

    type RuleGroup = {
      groupName: string,
      vendorName: string,
      excludedRules: string[],
      enableRequestSampling: boolean
    }


    if ( managedRules !== "dummy"){
      let ruleList: any[] = []

      managedRules.forEach((rule: RuleGroup, index: number) => {

        let ruleActionOverrides = []

        for (let excludedRule of rule.excludedRules) {
          let excludedRuleObj = {
            actionToUse: {
              count: {}
            },
            name: excludedRule
          }

          ruleActionOverrides.push(excludedRuleObj)
        }

        let managedRuleGroup: aws_wafv2.CfnWebACL.RuleProperty = {
          name: "managed-rule-group-" + rule.groupName,
          priority: 5 + index,
          overrideAction: {
            none: {}
          },
          statement: {
            managedRuleGroupStatement: {
              name: rule.groupName,
              vendorName: rule.vendorName,
              ruleActionOverrides: ruleActionOverrides
            }
          },
          visibilityConfig: {
            cloudWatchMetricsEnabled: true,
            metricName: "request-managed-rule-group-" + rule.groupName,
            sampledRequestsEnabled: rule.enableRequestSampling
          }
        }


        ruleList.push(managedRuleGroup)

      })

      rules = rules.concat(ruleList)
    }


    const cfnWebAcl = new aws_wafv2.CfnWebACL(this, 'WAFWebACL', {
      scope: "CLOUDFRONT",
      defaultAction: {
        allow: {}
      },
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: "DVVWAF",
        sampledRequestsEnabled: props.requestSampleAllTrafficEnabled
      },
      rules: rules
    })

    const WafAutomationArn = aws_ssm.StringParameter.fromStringParameterName(this, 'WafAutomationArn',
      `/${props.environment}/waf/waf_automation_arn`);

    const WafAutomationLambdaFunction = aws_lambda.Function.fromFunctionArn(this, "WafAutomation", WafAutomationArn.stringValue)

    const SNSTopicArn = aws_ssm.StringParameter.fromStringParameterName(this, 'SNSTopicArn',
      `/${props.environment}/waf/sns_topic_arn`);


    const topic =  aws_sns.Topic.fromTopicArn(this, "SNSTopic", SNSTopicArn.stringValue)

    topic.addSubscription(new aws_sns_subscriptions.LambdaSubscription(WafAutomationLambdaFunction))

  }
}
