import {
  aws_lambda,
  aws_shield,
  aws_sns,
  aws_ssm,
  aws_wafv2,
  Stack, Token, CfnParameter, aws_sns_subscriptions, aws_route53, Duration, Arn
} from "aws-cdk-lib";
import {Construct} from "constructs";

import {ShieldStackProps} from "./shield-stack-props";

import { z } from "zod";
import { HealthCheckType } from "aws-cdk-lib/aws-route53";

export class ShieldStack extends Stack {
  constructor(scope: Construct, id: string, props: ShieldStackProps) {
    super(scope, id, props);

    const nginxHealthCheck = new aws_route53.HealthCheck(this, 'nginxHealthCheck', {
      type: HealthCheckType.HTTPS,
      fqdn: props.fqdn,
      port: 443,
      resourcePath: '/health',
      failureThreshold: 3,
      requestInterval: Duration.seconds(30)
    })

    const ckanHealthCheck = new aws_route53.HealthCheck(this, 'ckanHealthCheck', {
      type: HealthCheckType.HTTPS,
      fqdn: props.fqdn,
      port: 443,
      resourcePath: '/data/api/action/status_show',
      failureThreshold: 3,
      requestInterval: Duration.seconds(30)
    })

    const drupalHealthCheck = new aws_route53.HealthCheck(this, 'drupalHealthCheck', {
      type: HealthCheckType.HTTPS,
      fqdn: props.fqdn,
      port: 443,
      resourcePath: '/fi',
      failureThreshold: 3,
      requestInterval: Duration.seconds(30)
    })

    const generateHealthCheckArn = ((healthCheckId: string, stack: Stack) => {
      return Arn.format({
        resource: 'healthCheck',
        service: 'route53',
        resourceName: healthCheckId
      }, stack)
    })

    const cfnProtection = new aws_shield.CfnProtection(this, 'ShieldProtection', {
      name: 'Application Load Balancers',
      resourceArn: props.loadBalancer.loadBalancerArn,
      healthCheckArns: [
        generateHealthCheckArn(ckanHealthCheck.healthCheckId, this)
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
            limit: Token.asNumber(props.highPriorityRateLimit.stringValue),
            aggregateKeyType: "IP",
            evaluationWindowSec: Token.asNumber(props.evaluationPeriod.stringValue),
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
            limit: Token.asNumber(props.rateLimit.stringValue),
            aggregateKeyType: "IP",
            evaluationWindowSec: Token.asNumber(props.evaluationPeriod.stringValue),
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

    const WafAutomationLambdaFunction = aws_lambda.Function.fromFunctionArn(this, "WafAutomation", props.wafAutomationArn.stringValue)
    
    const topic =  aws_sns.Topic.fromTopicArn(this, "SNSTopic", props.snsTopicArn.stringValue)

    topic.addSubscription(new aws_sns_subscriptions.LambdaSubscription(WafAutomationLambdaFunction))

  }
}
