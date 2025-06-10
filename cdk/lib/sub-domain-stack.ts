import {aws_iam, aws_route53, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {SubDomainStackProps} from "./sub-domain-stack-props";
import { IHostedZone } from "aws-cdk-lib/aws-route53";

export class SubDomainStack extends Stack {
    readonly subZone: aws_route53.PublicHostedZone;
    readonly zones: IHostedZone[];

    constructor(scope: Construct, id: string, props: SubDomainStackProps) {
        super(scope, id, props);

        this.subZone = new aws_route53.PublicHostedZone(this, 'SubZone', {
            zoneName: `${props.subDomainName}.avoindata.suomi.fi`
        })

        const delegationRoleArn = Stack.of(this).formatArn({
            region: '',
            service: 'iam',
            account: props.prodAccountId,
            resource: 'role',
            resourceName: 'Route53CrossDelegateRole'
        })

        const delegationRole = aws_iam.Role.fromRoleArn(this, 'delegationRole', delegationRoleArn)

        new aws_route53.CrossAccountZoneDelegationRecord(this, 'delegate', {
            delegatedZone: this.subZone,
            delegationRole: delegationRole,
            parentHostedZoneName: "avoindata.suomi.fi"
        })

        this.zones = [this.subZone];
    }

}
