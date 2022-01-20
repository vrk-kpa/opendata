import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { EnvProps } from './env-props';

export interface CommonStackProps extends StackProps {
  envProps: EnvProps;
  environment: string;
  fqdn: string;
  secondaryFqdn: string;
  domainName: string;
  secondaryDomainName: string;
}