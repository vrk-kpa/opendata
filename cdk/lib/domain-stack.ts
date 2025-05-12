import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_iam, aws_route53, aws_kms} from "aws-cdk-lib";
import {DomainStackProps} from "./domain-stack-props";

export class DomainStack extends cdk.Stack {
  readonly publicZone: aws_route53.PublicHostedZone;
  readonly dnssecKey: aws_kms.IKey;
  
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

    // DNSSEC
    this.dnssecKey = new aws_kms.Key(this, 'DNSSECKey', {
      enableKeyRotation: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      keySpec: aws_kms.KeySpec.ECC_NIST_P256,
      keyUsage: aws_kms.KeyUsage.SIGN_VERIFY,
    });

    
    this.dnssecKey.addToResourcePolicy(new aws_iam.PolicyStatement({
      sid: "AllowRoute53DNSSECService",
      effect: aws_iam.Effect.ALLOW,
      principals: [new aws_iam.ServicePrincipal("dnssec-route53.amazonaws.com")],
      actions: ["kms:DescribeKey", "kms:GetPublicKey", "kms:Sign"],
      resources: ["*"],
      conditions: {
        "StringEquals": { "aws:SourceAccount": cdk.Aws.ACCOUNT_ID }
      }
    }));       

    
    this.dnssecKey.addToResourcePolicy(new aws_iam.PolicyStatement({
      sid: "AllowRoute53DNSSECToCreateGrant",
      effect: aws_iam.Effect.ALLOW,
      principals: [new aws_iam.ServicePrincipal("dnssec-route53.amazonaws.com")],
      actions: ["kms:CreateGrant"],
      resources: ["*"],
      conditions: {
        "StringEquals": { "aws:SourceAccount": cdk.Aws.ACCOUNT_ID },
        "Bool": { "kms:GrantIsForAWSResource": true }
      }
    }));

    // Public zone
    const publicZoneKeySigningKey = new aws_route53.CfnKeySigningKey(this, 'PublicZoneKeySigningKey', {
      hostedZoneId: this.publicZone.hostedZoneId,
      keyManagementServiceArn: this.dnssecKey.keyArn,
      name: 'public-zone-dnssec-key',
      status: 'ACTIVE'
    });

    const publicZoneDnssec = new aws_route53.CfnDNSSEC(this, 'PublicZoneDNSSEC', {
      hostedZoneId: this.publicZone.hostedZoneId
    });
    publicZoneDnssec.node.addDependency(publicZoneKeySigningKey);

    // Opendata zone
    const opendataZone = aws_route53.HostedZone.fromLookup(this, 'OpendataZone', {
      domainName: props.fqdn
    })

    const opendataZoneKeySigningKey = new aws_route53.CfnKeySigningKey(this, 'OpendataZoneKeySigningKey', {
      hostedZoneId: opendataZone.hostedZoneId,
      keyManagementServiceArn: this.dnssecKey.keyArn,
      name: 'opendata-zone-dnssec-key',
      status: 'ACTIVE'
    });
    const opendataZoneDnssec = new aws_route53.CfnDNSSEC(this, 'OpendataZoneDNSSEC', {
      hostedZoneId: opendataZone.hostedZoneId
    });
    opendataZoneDnssec.node.addDependency(opendataZoneKeySigningKey);

    // Secondary Opendata zone
    const secondaryOpendataZone = aws_route53.HostedZone.fromLookup(this, 'SecondaryOpendataZone', {
      domainName: props.secondaryFqdn
    })

    const secondaryOpendataZoneKeySigningKey = new aws_route53.CfnKeySigningKey(this, 'SecondaryOpendataZoneKeySigningKey', {
      hostedZoneId: secondaryOpendataZone.hostedZoneId,
      keyManagementServiceArn: this.dnssecKey.keyArn,
      name: 'secondary-opendata-zone-dnssec-key',
      status: 'ACTIVE'
    });
    const secondaryOpendataZoneDnssec = new aws_route53.CfnDNSSEC(this, 'SecondaryOpendataZoneDNSSEC', {
      hostedZoneId: secondaryOpendataZone.hostedZoneId
    });
    secondaryOpendataZoneDnssec.node.addDependency(secondaryOpendataZoneKeySigningKey);

  }
}
