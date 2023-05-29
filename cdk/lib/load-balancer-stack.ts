import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import { Construct } from 'constructs';

import { ElbStackProps } from './elb-stack-props';

export class LoadBalancerStack extends Stack {
  readonly loadBalancerCert: acm.ICertificate;
  readonly loadBalancer: elb.IApplicationLoadBalancer;

  constructor(scope: Construct, id: string, props: ElbStackProps) {
    super(scope, id, props);

    // get params
    ssm.StringParameter.fromStringParameterAttributes(this, 'pLbCertArn', {
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

    this.loadBalancerCert = props.cert;

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
