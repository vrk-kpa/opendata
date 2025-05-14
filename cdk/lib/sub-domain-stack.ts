import {aws_iam, aws_route53, aws_route53_targets, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {SubDomainStackProps} from "./sub-domain-stack-props";

export class SubDomainStack extends Stack {
    readonly subZone: aws_route53.PublicHostedZone;
    readonly newSubZone: aws_route53.PublicHostedZone;
    constructor(scope: Construct, id: string, props: SubDomainStackProps) {
        super(scope, id, props);

        this.subZone = new aws_route53.PublicHostedZone(this, 'SubZone', {
            zoneName: props.subDomainName + ".avoindata.suomi.fi"
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

        // DNSSEC
        const subZoneKeySigningKey = new aws_route53.CfnKeySigningKey(this, 'SubZoneKeySigningKey', {
          hostedZoneId: this.subZone.hostedZoneId,
          keyManagementServiceArn: props.dnssecKey.keyArn,
          name: 'sub-zone-dnssec-key',
          status: 'ACTIVE'
        });

        const subZoneDnssec = new aws_route53.CfnDNSSEC(this, 'SubZoneDNSSEC', {
          hostedZoneId: this.subZone.hostedZoneId
        });
        subZoneDnssec.node.addDependency(subZoneKeySigningKey);
    }

}
