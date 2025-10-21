import {
  aws_lambda,
  aws_shield,
  aws_sns,
  aws_ssm,
  aws_wafv2,
  Stack, Token, CfnParameter, aws_sns_subscriptions, aws_cloudwatch, aws_route53
} from "aws-cdk-lib";
import {Construct} from "constructs";

import {ShieldStackProps} from "./shield-stack-props";

import { z } from "zod";

export class ShieldStack extends Stack {
  constructor(scope: Construct, id: string, props: ShieldStackProps) {
    super(scope, id, props);

    const targetResponseTimeAlarm = new aws_cloudwatch.Alarm(this, 'targetResponseTimeAlarm', {
      metric: props.loadBalancer.metrics.targetResponseTime({
        statistic: aws_cloudwatch.Stats.AVERAGE
      }),
      evaluationPeriods: 1,
      threshold: 10,
      alarmName: "TargetResponseTimeAlarm"
    })


    const healthCheck = new aws_route53.HealthCheck(this, 'healthCheck', {
      type: aws_route53.HealthCheckType.CLOUDWATCH_METRIC,
      alarmIdentifier: {
        name: targetResponseTimeAlarm.alarmName,
        region: "eu-west-1"
      },
      
    })

    const cfnProtection = new aws_shield.CfnProtection(this, 'ShieldProtection', {
      name: 'Application Load Balancers',
      resourceArn: props.loadBalancer.loadBalancerArn,
      healthCheckArns: [
        `arn:aws:route53:::healthcheck/${healthCheck.healthCheckId}`
      ]
    })
    

    const banned_ips = new CfnParameter(this, 'bannedIpsList', {
      type: 'AWS::SSM::Parameter::Value<List<String>>',
      default: props.bannedIpListParameterName
    })

    const cfnBannedIPSet = new aws_wafv2.CfnIPSet(this, 'BannedIPSet', {
      name: 'banned-ips',
      scope: 'REGIONAL',
      ipAddressVersion: "IPV4",
      addresses: banned_ips.valueAsList
    })

    const whitelisted_ips = new CfnParameter(this, 'whitelistedIpsList', {
      type: 'AWS::SSM::Parameter::Value<List<String>>',
      default: props.whitelistedIpListParameterName
    })

    const cfnWhiteListedIpSet = new aws_wafv2.CfnIPSet(this, 'WhitelistedIPSet', {
      name: 'whitelisted-ips',
      scope: 'REGIONAL',
      ipAddressVersion: "IPV4",
      addresses: whitelisted_ips.valueAsList
    })


    const highPriorityCountryCodesParameter = new CfnParameter(this,  'highPriorityCountryCodesParameter', {
      type: 'AWS::SSM::Parameter::Value<List<String>>',
      default: props.highPriorityCountryCodeListParameterName
    });


    const highPriorityRateLimitParameter = aws_ssm.StringParameter.fromStringParameterAttributes(this, 'highPriorityRateLimitParameter', {
      parameterName: props.highPriorityRateLimitParameterName,
      simpleName: false
    });
  
    const rateLimitParameter = aws_ssm.StringParameter.fromStringParameterAttributes(this, 'rateLimitParameter', {
      parameterName: props.rateLimitParameterName,
      simpleName: false
    });
  
    const wafAutomationArnParameter = aws_ssm.StringParameter.fromStringParameterAttributes(this, 'wafAutomationArnParameter', {
      parameterName: props.wafAutomationArnParameterName,
      simpleName: false
    });
  
    const snsTopicArnParameter = aws_ssm.StringParameter.fromStringParameterAttributes(this, 'snsTopicArnParameter', {
      parameterName: props.snsTopicArnParameterName,
      simpleName: false
    });
  
    const evaluationPeriodParameter = aws_ssm.StringParameter.fromStringParameterAttributes(this, 'evaluationPeriodParameter', {
      parameterName: props.evaluationPeriodParameterName,
      simpleName: false
    });
  

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
            limit: Token.asNumber(highPriorityRateLimitParameter.stringValue),
            aggregateKeyType: "IP",
            evaluationWindowSec: Token.asNumber(evaluationPeriodParameter.stringValue),
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
            limit: Token.asNumber(rateLimitParameter.stringValue),
            aggregateKeyType: "IP",
            evaluationWindowSec: Token.asNumber(evaluationPeriodParameter.stringValue),
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

    const RuleGroupSchema = z.array(
      z.object(
        {
          groupName: z.string(),
          vendorName: z.string(),
          ruleActionOverrideCounts: z.array(z.string()).default([]),
          ruleActionOverrideAllows: z.array(z.string()).default([]),
          ruleActionOverrideBlocks: z.array(z.string()).default([]),
          ruleActionOverrideCaptchas: z.array(z.string()).default([]),
          ruleActionOverrideChallenges: z.array(z.string()).default([]),
          enableRequestSampling: z.boolean()
        }
      ).strict()
    )


    const managedRulesParameter = aws_ssm.StringParameter.valueFromLookup(this, props.managedRulesParameterName)

    const managedRules = managedRulesParameter.startsWith("dummy-value") ? "dummy" : JSON.parse(managedRulesParameter)


    if ( managedRules !== "dummy"){
      let ruleList: any[] = []
      const validatedRules = RuleGroupSchema.parse(managedRules)
      validatedRules.forEach((rule, index: number) => {

        let ruleActionOverrides = []

        for (let overrideCountRule of rule.ruleActionOverrideCounts) {
          let overrideCountRuleObj = {
            actionToUse: {
              count: {}
            },
            name: overrideCountRule
          }

          ruleActionOverrides.push(overrideCountRuleObj)
        }

        for ( let overrideAllowRule of rule.ruleActionOverrideAllows) {
          let overrideAllowRuleObj = {
            actionToUse: {
              allow: {}
            },
            name: overrideAllowRule
          }

          ruleActionOverrides.push(overrideAllowRuleObj)
        }

        for ( let overrideBlockRule of rule.ruleActionOverrideBlocks) {
          let overrideBlockRuleObj = {
            actionToUse: {
              block: {}
            },
            name: overrideBlockRule
          }

          ruleActionOverrides.push(overrideBlockRuleObj)
        }
        for ( let overrideCaptchaRule of rule.ruleActionOverrideCaptchas) {
          let overrideCaptchaRuleObj = {
            actionToUse: {
              captcha: {}
            },
            name: overrideCaptchaRule
          }

          ruleActionOverrides.push(overrideCaptchaRuleObj)
        }
        for ( let overrideChallengeRule of rule.ruleActionOverrideChallenges) {
          let overrideChallengeRuleObj = {
            actionToUse: {
              challenge: {}
            },
            name: overrideChallengeRule
          }

          ruleActionOverrides.push(overrideChallengeRuleObj)
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


    const blockedUserAgentsParameter = aws_ssm.StringParameter.valueFromLookup(this, props.blockedUserAgentsParameterName, '[]')
    const blockedUserAgentsJson = JSON.parse(blockedUserAgentsParameter)

    const BlockedUserAgentsSchema = z.array(z.string())

    let blockedUserAgentRules: any[] = []
    const validatedUserAgents = BlockedUserAgentsSchema.parse(blockedUserAgentsJson)
    validatedUserAgents.forEach((useragent, index: number) => {
      let blockedUserAgentRule: aws_wafv2.CfnWebACL.RuleProperty = {
        name: "blocked-useragent-" + useragent,
        priority: rules.length + index,
        action: {
          block: {}
        },
        statement: {
          byteMatchStatement: {
            fieldToMatch: {
              singleHeader: {
                name: "User-Agent"
              }
            },
            positionalConstraint: "CONTAINS",
            searchString: useragent,
            textTransformations: [
              {
                type: "NONE",
                priority: 0
              }
            ]
          }
        },
        visibilityConfig: {
          cloudWatchMetricsEnabled: true,
          metricName: "blocked-useragent-" + useragent,
          sampledRequestsEnabled: false
        }
      }

      blockedUserAgentRules.push(blockedUserAgentRule)
    })

    rules = rules.concat(blockedUserAgentRules)


    const cfnWebAcl = new aws_wafv2.CfnWebACL(this, 'WAFWebACL', {
      scope: "REGIONAL",
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

    new aws_wafv2.CfnWebACLAssociation(this, 'WafAssociation', {
      resourceArn: props.loadBalancer.loadBalancerArn,
      webAclArn: cfnWebAcl.attrArn
    })

    const WafAutomationLambdaFunction = aws_lambda.Function.fromFunctionArn(this, "WafAutomation", wafAutomationArnParameter.stringValue)
    
    const topic =  aws_sns.Topic.fromTopicArn(this, "SNSTopic", snsTopicArnParameter.stringValue)

    topic.addSubscription(new aws_sns_subscriptions.LambdaSubscription(WafAutomationLambdaFunction))

  }
}
