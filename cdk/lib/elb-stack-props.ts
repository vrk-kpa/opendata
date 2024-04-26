import {aws_ec2 as ec2, aws_certificatemanager as acm} from 'aws-cdk-lib';


import {EnvStackProps} from "./env-stack-props";

export interface ElbStackProps extends EnvStackProps {
  vpc: ec2.IVpc;
}
