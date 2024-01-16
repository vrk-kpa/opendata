import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { CkanStack } from '../lib/ckan-stack';
import { BackupStack} from "../lib/backup-stack";
import { mockEnv, mockEnvProps } from './mock-constructs';
import {data} from "aws-cdk/lib/logging";
import {LambdaStack} from "../lib/lambda-stack";


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
    vpcId: 'someid'
  });

  const backupStack = new BackupStack(app, 'BackupStack-Test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    backups: true,
    importVault: false
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
    backupPlan: backupStack.backupPlan,
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
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });

  const lambdaStack = new LambdaStack(app, 'LambdaStack-test', {
    envProps: mockEnvProps,
    env: mockEnv,
    environment: 'mock-env',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',
    datastoreInstance: databaseStack.datastoreInstance,
    datastoreCredentials: databaseStack.datastoreCredentials,
    vpc: clusterStack.vpc
  })

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
      'fuseki': fileSystemStack.fusekiFs,
    },
    migrationFileSystemProps: {
      securityGroup: fileSystemStack.migrationFsSg!,
      fileSystem: fileSystemStack.migrationFs!,
    },
    databaseSecurityGroup: databaseStack.databaseSecurityGroup,
    databaseInstance: databaseStack.databaseInstance,
    datastoreInstance: databaseStack.datastoreInstance,
    datastoreCredentials: databaseStack.datastoreCredentials,
    datastoreJobsCredentials: lambdaStack.datastoreJobsCredentials,
    datastoreReadCredentials: lambdaStack.datastoreReadCredentials,
    datastoreUserCredentials: lambdaStack.datastoreUserCredentials,
    datastoreSecurityGroup: databaseStack.datastoreSecurityGroup,
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
    fusekiTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 0,
      taskMaxCapacity: 1,
    },
    ckanUwsgiProps: {
      processes: 2,
      threads: 2
    },
    ckanCronEnabled: true,
    archiverSendNotificationEmailsToMaintainers: false,
    archiverExemptDomainsFromBrokenLinkNotifications: [],
    cloudstorageEnabled: true,
  });
  // THEN
  const template = Template.fromStack(stack);
  template.hasResource('AWS::ECS::Service', {});
  // TODO: write more in-depth resource verification here...
});
