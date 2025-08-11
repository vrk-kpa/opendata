import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_route53} from "aws-cdk-lib";
import {DnssecStackProps} from "./dnssec-stack-props";

export class DnssecStack extends cdk.Stack {

  constructor(scope: Construct, id: string, props: DnssecStackProps) {
    super(scope, id, props);

    for(const zone of props.zones) {
      let mungedName = zone.zoneName.replace(new RegExp('[^a-zA-Z0-9]', 'g'), '')
      const zoneKeySigningKey = new aws_route53.CfnKeySigningKey(this, `KeySigningKey-${mungedName}`, {
        hostedZoneId: zone.hostedZoneId,
        keyManagementServiceArn: `arn:aws:kms:us-east-1:${cdk.Aws.ACCOUNT_ID}:alias/${props.keyAlias}`,
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
