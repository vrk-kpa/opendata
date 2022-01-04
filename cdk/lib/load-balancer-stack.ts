import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';
import * as elb from '@aws-cdk/aws-elasticloadbalancingv2';
import * as efs from '@aws-cdk/aws-efs';
import * as ssm from '@aws-cdk/aws-ssm';
import * as sm from '@aws-cdk/aws-secretsmanager';
import * as ec from '@aws-cdk/aws-elasticache';
import * as acm from '@aws-cdk/aws-certificatemanager';

import { ElbStackProps } from './elb-stack-props';

export class LoadBalancerStack extends cdk.Stack {
  readonly loadBalancerCert: acm.ICertificate;
  readonly loadBalancer: elb.IApplicationLoadBalancer;

  constructor(scope: cdk.Construct, id: string, props: ElbStackProps) {
    super(scope, id, props);

    // get params
    const pLbCertArn = ssm.StringParameter.fromStringParameterAttributes(this, 'pLbCertArn', {
      parameterName: `/${props.environment}/opendata/cdk/lb_cert_arn`,
    });
    const pLbArn = ssm.StringParameter.fromStringParameterAttributes(this, 'pLbArn', {
      parameterName: `/${props.environment}/opendata/cdk/lb_arn`,
    });
    const pLbSgId = ssm.StringParameter.fromStringParameterAttributes(this, 'pLbSgId', {
      parameterName: `/${props.environment}/opendata/cdk/lb_sg_id`,
    });
    const pLbCanonicalHostedZoneId = ssm.StringParameter.fromStringParameterAttributes(this, 'pLbCanonicalHostedZoneId', {
      parameterName: `/${props.environment}/opendata/cdk/lb_canonical_hosted_zone_id`,
    });
    const pLbDnsName = ssm.StringParameter.fromStringParameterAttributes(this, 'pLbDnsName', {
      parameterName: `/${props.environment}/opendata/cdk/lb_dns_name`,
    });

    this.loadBalancerCert = acm.Certificate.fromCertificateArn(this, 'loadBalancerCert', pLbCertArn.stringValue);

    this.loadBalancer = elb.ApplicationLoadBalancer.fromApplicationLoadBalancerAttributes(this, 'loadBalancer', {
      loadBalancerArn: pLbArn.stringValue,
      securityGroupId: pLbSgId.stringValue,
      loadBalancerCanonicalHostedZoneId: pLbCanonicalHostedZoneId.stringValue,
      loadBalancerDnsName: pLbDnsName.stringValue,
      securityGroupAllowsAllOutbound: true,
      vpc: props.vpc,
    });

  }
}