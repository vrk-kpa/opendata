import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_iam, aws_route53} from "aws-cdk-lib";
import {DomainStackProps} from "./domain-stack-props";
import { IHostedZone } from "aws-cdk-lib/aws-route53";

export class DomainStack extends cdk.Stack {
  readonly publicZone: aws_route53.PublicHostedZone;
  readonly zones: IHostedZone[];
  
  constructor(scope: Construct, id: string, props: DomainStackProps) {
    super(scope, id, props);

    this.publicZone = new aws_route53.PublicHostedZone(this, "HostedZone", {
      zoneName: props.zoneName,
    })
    
    if (props.crossAccountId) {
      const role = new aws_iam.Role(this, 'Route53CrossDelegateRole', {
        assumedBy: new aws_iam.AccountPrincipal(props.crossAccountId),
        roleName: "Route53CrossDelegateRole"
      })

      this.publicZone.grantDelegation(role)
    }

    const opendataZone = aws_route53.HostedZone.fromLookup(this, 'OpendataZone', {
      domainName: props.fqdn
    })
    const secondaryOpendataZone = aws_route53.HostedZone.fromLookup(this, 'SecondaryOpendataZone', {
      domainName: props.secondaryFqdn
    })

    this.zones = [this.publicZone, opendataZone, secondaryOpendataZone];
    if (props.tertiaryFqdn) {
      const tertiaryOpendataZone = aws_route53.HostedZone.fromLookup(this, 'tertiaryOpendataZone', {
        domainName: props.tertiaryFqdn
      })
      this.zones.push(tertiaryOpendataZone)
    }
  }
}
