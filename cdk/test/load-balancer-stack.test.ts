import {
  expect as expectCDK,
  matchTemplate,
  MatchStyle,
  haveResource,
  countResources,
  countResourcesLike
} from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import { ClusterStack } from '../lib/cluster-stack';
import { LoadBalancerStack } from '../lib/load-balancer-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';

test('verify load balancer stack resources', () => {
  const app = new cdk.App();
  const clusterStack = new ClusterStack(app, 'ClusterStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
  });
  // WHEN
  const stack = new LoadBalancerStack(app, 'LoadBalancerStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    vpc: clusterStack.vpc,
  });
  // THEN
  // no actual resources to verify
});
