import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_iam, aws_kms} from "aws-cdk-lib";
import {DnssecKeyStackProps} from "./dnssec-key-stack-props";

export class DnssecKeyStack extends cdk.Stack {

  constructor(scope: Construct, id: string, props: DnssecKeyStackProps) {
    super(scope, id, props);

    const dnssecKey = new aws_kms.Key(this, 'DNSSECKey', {
      alias: props.keyAlias,
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
  }
}

