import * as cdk from '@aws-cdk/core';

export interface CommonStackProps extends cdk.StackProps {
  environment: string;
  fqdn: string;
  secondaryFqdn: string;
  domainName: string;
  secondaryDomainName: string;
}