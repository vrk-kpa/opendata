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
import { FileSystemStack } from '../lib/filesystem-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';

test('verify filesystem stack resources', () => {
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
  const stack = new FileSystemStack(app, 'FileSystemStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    vpc: clusterStack.vpc,
    importMigrationFs: true,
  });
  // THEN
  expectCDK(stack).to(countResources('AWS::EC2::SecurityGroup', 3));
  expectCDK(stack).to(countResources('AWS::EFS::MountTarget', 6));
  expectCDK(stack).to(countResourcesLike('AWS::EFS::FileSystem', 3, {
    PerformanceMode: 'generalPurpose',
    ThroughputMode: 'bursting'
  }));
});
