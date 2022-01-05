import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';

test('verify cluster stack resources', () => {
  const app = new cdk.App();
  // WHEN
  const stack = new ClusterStack(app, 'ClusterStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
  });
  // THEN
  const template = Template.fromStack(stack);
  template.hasResource('AWS::ECS::Cluster', {});
  template.hasResourceProperties('AWS::ECS::ClusterCapacityProviderAssociations', {
    CapacityProviders: [
      'FARGATE',
      'FARGATE_SPOT',
    ],
  });
  template.hasResource('AWS::ServiceDiscovery::PrivateDnsNamespace', {});
});
