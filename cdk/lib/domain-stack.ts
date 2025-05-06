import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_iam, aws_route53, aws_kms} from "aws-cdk-lib";
import {DomainStackProps} from "./domain-stack-props";

export class DomainStack extends cdk.Stack {
  readonly publicZone: aws_route53.PublicHostedZone;
  constructor(scope: Construct, id: string, props: DomainStackProps) {
    super(scope, id, props);

    
    const dnssecKey = new aws_kms.Key(this, 'DNSSECKey', {
      enableKeyRotation: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      keySpec: aws_kms.KeySpec.ECC_NIST_P256,
      keyUsage: aws_kms.KeyUsage.SIGN_VERIFY,
    });

    
    dnssecKey.addToResourcePolicy(new aws_iam.PolicyStatement({
      sid: "AllowRoute53DNSSECService",
      effect: aws_iam.Effect.ALLOW,
      principals: [new aws_iam.ServicePrincipal("dnssec-route53.amazonaws.com")],
      actions: ["kms:DescribeKey", "kms:GetPublicKey", "kms:Sign"],
      resources: ["*"],
      conditions: {
        "StringEquals": { "aws:SourceAccount": cdk.Aws.ACCOUNT_ID }
      }
    }));       

    
    dnssecKey.addToResourcePolicy(new aws_iam.PolicyStatement({
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


    this.publicZone = new aws_route53.PublicHostedZone(this, "HostedZone", {
      zoneName: props.zoneName,
    })

    
    const keySigningKey = new aws_route53.CfnKeySigningKey(this, 'KeySigningKey', {
      hostedZoneId: this.publicZone.hostedZoneId,
      keyManagementServiceArn: dnssecKey.keyArn,
      name: 'public-zone-dnssec-key',
      status: 'ACTIVE'
    });

    const dnssec = new aws_route53.CfnDNSSEC(this, 'PublicZoneDNSSEC', {
      hostedZoneId: this.publicZone.hostedZoneId
    });
    dnssec.node.addDependency(keySigningKey);

    if (props.crossAccountId) {
      const role = new aws_iam.Role(this, 'Route53CrossDelegateRole', {
        assumedBy: new aws_iam.AccountPrincipal(props.crossAccountId),
        roleName: "Route53CrossDelegateRole"
      })

      this.publicZone.grantDelegation(role)
    }
  }
}
