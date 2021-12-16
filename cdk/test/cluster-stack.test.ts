import {
  expect as expectCDK,
  matchTemplate,
  MatchStyle,
  haveResource
} from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
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
  expectCDK(stack).to(haveResource('AWS::ECS::Cluster'));
  expectCDK(stack).to(haveResource('AWS::ECS::ClusterCapacityProviderAssociations', {
    CapacityProviders: [
      'FARGATE',
      'FARGATE_SPOT',
    ],
  }));
  expectCDK(stack).to(haveResource('AWS::ServiceDiscovery::PrivateDnsNamespace'));
});
