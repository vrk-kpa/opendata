import { EnvProps } from './env-props';
import * as cdk from '@aws-cdk/core';

export interface CommonStackProps extends cdk.StackProps {
  envProps: EnvProps;
  environment: string;
  fqdn: string;
  secondaryFqdn: string;
  domainName: string;
  secondaryDomainName: string;
}