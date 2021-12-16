import {
  expect as expectCDK,
  matchTemplate,
  MatchStyle,
  haveResource
} from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import { ClusterStack } from '../lib/cluster-stack';
import { CacheStack } from '../lib/cache-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';

test('verify cache stack resources', () => {
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
  const stack = new CacheStack(app, 'CacheStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    vpc: clusterStack.vpc,
    cacheNodeType: 'cache.t2.micro',
    cacheEngineVersion: '6.x',
    cacheNumNodes: 4,
  });
  // THEN
  expectCDK(stack).to(haveResource('AWS::ElastiCache::SubnetGroup'));
  expectCDK(stack).to(haveResource('AWS::EC2::SecurityGroup'));
  expectCDK(stack).to(haveResource('AWS::ElastiCache::CacheCluster', {
    CacheNodeType: 'cache.t2.micro',
    NumCacheNodes: 4,
    EngineVersion: '6.x'
  }));
});
