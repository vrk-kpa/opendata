import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {aws_iam, aws_route53, Stack} from "aws-cdk-lib";
import {DomainStackProps} from "./domain-stack-props";
import { IHostedZone } from "aws-cdk-lib/aws-route53";

export class DomainStack extends cdk.Stack {
  readonly publicZone: aws_route53.PublicHostedZone;

  constructor(scope: Construct, id: string, props: DomainStackProps) {
    super(scope, id, props);

    this.publicZone = new aws_route53.PublicHostedZone(this, "HostedZone", {
      zoneName: props.zoneName,
    })

    // prod stack
    if (props.crossAccountId) {
      const role = new aws_iam.Role(this, 'Route53CrossDelegateRole', {
        assumedBy: new aws_iam.AccountPrincipal(props.crossAccountId),
        roleName: "Route53CrossDelegateRole"
      })

      this.publicZone.grantDelegation(role)
    }

    // dev stack
    if (props.prodAccountId ) {
      const delegationRoleArn = Stack.of(this).formatArn({
        region: '',
        service: 'iam',
        account: props.prodAccountId,
        resource: 'role',
        resourceName: 'Route53CrossDelegateRole'
      })

      const delegationRole = aws_iam.Role.fromRoleArn(this, 'delegationRole', delegationRoleArn)

      new aws_route53.CrossAccountZoneDelegationRecord(this, 'delegate', {
        delegatedZone: this.publicZone,
        delegationRole: delegationRole,
        parentHostedZoneName: "avoindata.suomi.fi"
      })
    }

  }
}
