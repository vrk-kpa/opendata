import {aws_kms, aws_route53, StackProps} from "aws-cdk-lib";
import {ApplicationLoadBalancer} from "aws-cdk-lib/aws-elasticloadbalancingv2";

export interface SubDomainStackProps extends StackProps {
    prodAccountId: string;
    subDomainName: string;
    dnssecKey: aws_kms.IKey
}
