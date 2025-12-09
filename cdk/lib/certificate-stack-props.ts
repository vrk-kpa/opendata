import {CommonStackProps} from "./common-stack-props";
import {aws_route53} from "aws-cdk-lib";
import {ElbStackProps} from "./elb-stack-props";
import {OldDomain} from "./env-props";

export interface CertificateStackProps extends ElbStackProps {
  zone: aws_route53.IHostedZone,
  rootFqdn: string,
  webFqdn: string,
  oldDomains: OldDomain[]
}
