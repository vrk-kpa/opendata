import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_iam, aws_route53, aws_kms} from "aws-cdk-lib";
import {DnssecStackProps} from "./dnssec-stack-props";

export class DnssecStack extends cdk.Stack {

  constructor(scope: Construct, id: string, props: DnssecStackProps) {
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

    for(const zone of props.zones) {
      let mungedName = zone.zoneName.replace(new RegExp('[^a-zA-Z0-9]', 'g'), '')
      const zoneKeySigningKey = new aws_route53.CfnKeySigningKey(this, `KeySigningKey-${mungedName}`, {
        hostedZoneId: zone.hostedZoneId,
        keyManagementServiceArn: dnssecKey.keyArn,
        name: `zone_${mungedName}_dnssec_key`,
        status: 'ACTIVE'
      });
      const zoneDnssec = new aws_route53.CfnDNSSEC(this, `DnsSec-${mungedName}`, {
        hostedZoneId: zone.hostedZoneId
      });
      zoneDnssec.node.addDependency(zoneKeySigningKey);
    }
  }
}
