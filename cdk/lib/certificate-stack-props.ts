import {CommonStackProps} from "./common-stack-props";
import {aws_route53} from "aws-cdk-lib";
import {ElbStackProps} from "./elb-stack-props";

export interface CertificateStackProps extends ElbStackProps {
  zone: aws_route53.IHostedZone
  alternativeZone: aws_route53.IHostedZone
}
