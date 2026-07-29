import {aws_ec2 as ec2, aws_certificatemanager as acm, aws_route53} from 'aws-cdk-lib';


import {EnvStackProps} from "./env-stack-props";
import {OldDomain} from "./env-props";

export interface ElbStackProps extends EnvStackProps {
  vpc: ec2.IVpc;
  rootFqdn: string;
  webFqdn: string;
  oldDomains: OldDomain[];
}
