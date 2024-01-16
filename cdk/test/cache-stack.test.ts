import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

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
    vpcId: 'someid'
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
  const template = Template.fromStack(stack);
  template.hasResource('AWS::ElastiCache::SubnetGroup', {});
  template.hasResource('AWS::EC2::SecurityGroup', {});
  template.hasResourceProperties('AWS::ElastiCache::CacheCluster', {
    CacheNodeType: 'cache.t2.micro',
    NumCacheNodes: 4,
    EngineVersion: '6.x'
  });
});
