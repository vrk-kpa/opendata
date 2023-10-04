import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_iam, aws_route53} from "aws-cdk-lib";
import {DomainStackProps} from "./domain-stack-props";

export class DomainStack extends cdk.Stack {
  readonly publicZone: aws_route53.PublicHostedZone;
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
  }
}
