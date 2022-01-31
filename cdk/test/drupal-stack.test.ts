import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { DrupalStack } from '../lib/drupal-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';

test('verify drupal stack resources', () => {
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
  const fileSystemStack = new FileSystemStack(app, 'FileSystemStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    vpc: clusterStack.vpc,
    backups: true,
    importMigrationFs: true,
  });
  const databaseStack = new DatabaseStack(app, 'DatabaseStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    vpc: clusterStack.vpc,
  });
  const cacheStack = new CacheStack(app, 'CacheStack-test', {
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
  // WHEN
  const stack = new DrupalStack(app, 'DrupalStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    vpc: clusterStack.vpc,
    cluster: clusterStack.cluster,
    namespace: clusterStack.namespace,
    fileSystems: {
      'drupal': fileSystemStack.drupalFs,
    },
    migrationFileSystemProps: {
      securityGroup: fileSystemStack.migrationFsSg!,
      fileSystem: fileSystemStack.migrationFs!,
    },
    databaseSecurityGroup: databaseStack.databaseSecurityGroup,
    databaseInstance: databaseStack.databaseInstance,
    cachePort: cacheStack.cachePort,
    cacheSecurityGroup: cacheStack.cacheSecurityGroup,
    cacheCluster: cacheStack.cacheCluster,
    captchaEnabled: true,
    analyticsEnabled: true,
    drupalTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 1,
      taskMaxCapacity: 2,
    },
  });
  // THEN
  const template = Template.fromStack(stack);
  template.hasResource('AWS::ECS::Service', {});
  // TODO: write more in-depth resource verification here...
});
