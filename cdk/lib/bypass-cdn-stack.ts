import {
  aws_route53 as route53,
  aws_route53_targets,
  aws_certificatemanager as acm
} from 'aws-cdk-lib';
import {Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {BypassCdnStackProps} from "./bypass-cdn-stack-props";

export class BypassCdnStack extends Stack {
  constructor(scope: Construct, id: string, props: BypassCdnStackProps) {
    super(scope, id, props);

    const zone = route53.HostedZone.fromLookup(this, 'OpendataZone', {
      domainName: props.fqdn
    })

    const alternateZone = route53.HostedZone.fromLookup(this, 'AlternateOpendataZone', {
      domainName: props.secondaryFqdn
    })

    let domain_record = new route53.ARecord(this, 'ARecord', {
      zone: zone,
      recordName: 'vip',
      target: route53.RecordTarget.fromAlias(new aws_route53_targets.LoadBalancerTarget(props.loadbalancer))
    })

    let root_record = new route53.ARecord(this, "rootRecord", {
      zone: zone,
      recordName: 'www',
      target: route53.RecordTarget.fromAlias(new aws_route53_targets.LoadBalancerTarget(props.loadbalancer))
    })

    let alternate_root_record = new route53.ARecord(this, "alternateRootRecord", {
      zone: alternateZone,
      recordName: 'www',
      target: route53.RecordTarget.fromAlias(new aws_route53_targets.LoadBalancerTarget(props.loadbalancer))
    })
  }
}


