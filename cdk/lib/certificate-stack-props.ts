import {CommonStackProps} from "./common-stack-props";
import {aws_route53} from "aws-cdk-lib";

export interface CertificateStackProps extends CommonStackProps {
  zone: aws_route53.IHostedZone
}
