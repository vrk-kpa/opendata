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
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { CkanStack } from '../lib/ckan-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';

test('verify ckan stack resources', () => {
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
  const stack = new CkanStack(app, 'CkanStack-test', {
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
      'ckan': fileSystemStack.ckanFs,
      'solr': fileSystemStack.solrFs,
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
    ckanTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 1,
      taskMaxCapacity: 2,
    },
    ckanCronTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 0,
      taskMaxCapacity: 1,
    },
    datapusherTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 1,
      taskMaxCapacity: 2,
    },
    solrTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 0,
      taskMaxCapacity: 1,
    },
    ckanCronEnabled: true,
    archiverSendNotificationEmailsToMaintainers: false,
    archiverExemptDomainsFromBrokenLinkNotifications: [],
    cloudstorageEnabled: true,
  });
  // THEN
  expectCDK(stack).to(haveResource('AWS::ECS::Service'));
  // TODO: write more in-depth resource verification here...
});
