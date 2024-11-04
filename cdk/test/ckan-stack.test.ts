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
    env: mockEnv,
    environment: 'mock-env',
    vpcId: 'someid'
  });

  const backupStack = new BackupStack(app, 'BackupStack-Test', {
    env: mockEnv,
    environment: 'mock-env',
    backups: true,
    importVault: false
  });

  const fileSystemStack = new FileSystemStack(app, 'FileSystemStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    importMigrationFs: true,
  });

  const databaseStack = new DatabaseStack(app, 'DatabaseStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });

  const lambdaStack = new LambdaStack(app, 'LambdaStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    datastoreInstance: databaseStack.datastoreInstance,
    datastoreCredentials: databaseStack.datastoreCredentials,
    vpc: clusterStack.vpc
  })

  const cacheStack = new CacheStack(app, 'CacheStack-test', {
    env: mockEnv,
    environment: 'mock-env',
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
    prhToolsInUse: false,
    archiverSendNotificationEmailsToMaintainers: false,
    archiverExemptDomainsFromBrokenLinkNotifications: [],
    cloudstorageEnabled: true,
    sentryTracesSampleRate: "1.0",
    sentryProfilesSampleRate: "1.0"
  });
  // THEN
  const template = Template.fromStack(stack);
  template.hasResource('AWS::ECS::Service', {});
  const taskDefs = template.findResources('AWS::ECS::TaskDefinition', {});
  const containerDefinitions = Object.values(taskDefs).flatMap(taskDef => taskDef.Properties.ContainerDefinitions);
  const environmentVariables = containerDefinitions.flatMap(containerDef => containerDef.Environment);
  const analyticsDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'MATOMO_ENABLED' || ev.Value === 'false')
  }, true);
  const captchaDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'CAPTCHA_ENABLED' || ev.Value === 'false')
  }, true);
  expect(analyticsDisabled).toBeFalsy();
  expect(captchaDisabled).toBeFalsy();
  // TODO: write more in-depth resource verification here...
});

test('create ckan stack without analytics', () => {
  const app = new cdk.App();
  const clusterStack = new ClusterStack(app, 'ClusterStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpcId: 'someid'
  });

  const backupStack = new BackupStack(app, 'BackupStack-Test', {
    env: mockEnv,
    environment: 'mock-env',
    backups: true,
    importVault: false
  });

  const fileSystemStack = new FileSystemStack(app, 'FileSystemStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    importMigrationFs: true,
  });

  const databaseStack = new DatabaseStack(app, 'DatabaseStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });

  const lambdaStack = new LambdaStack(app, 'LambdaStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    datastoreInstance: databaseStack.datastoreInstance,
    datastoreCredentials: databaseStack.datastoreCredentials,
    vpc: clusterStack.vpc
  })

  const cacheStack = new CacheStack(app, 'CacheStack-test', {
    env: mockEnv,
    environment: 'mock-env',
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
    analyticsEnabled: false,
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
    prhToolsInUse: false,
    archiverSendNotificationEmailsToMaintainers: false,
    archiverExemptDomainsFromBrokenLinkNotifications: [],
    cloudstorageEnabled: true,
    sentryTracesSampleRate: "1.0",
    sentryProfilesSampleRate: "1.0"
  });
  // THEN
  const template = Template.fromStack(stack);
  template.hasResource('AWS::ECS::Service', {});
  const taskDefs = template.findResources('AWS::ECS::TaskDefinition', {});
  const containerDefinitions = Object.values(taskDefs).flatMap(taskDef => taskDef.Properties.ContainerDefinitions);
  const environmentVariables = containerDefinitions.flatMap(containerDef => containerDef.Environment).filter(ev => ev !== undefined);
  const analyticsDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'MATOMO_ENABLED' || ev.Value === 'false')
  }, true);
  const captchaDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'CAPTCHA_ENABLED' || ev.Value === 'false')
  }, true);
  expect(analyticsDisabled).toBeTruthy();
  expect(captchaDisabled).toBeFalsy();
  // TODO: write more in-depth resource verification here...
});
test('create ckan stack without captcha', () => {
  const app = new cdk.App();
  const clusterStack = new ClusterStack(app, 'ClusterStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpcId: 'someid'
  });

  const backupStack = new BackupStack(app, 'BackupStack-Test', {
    env: mockEnv,
    environment: 'mock-env',
    backups: true,
    importVault: false
  });

  const fileSystemStack = new FileSystemStack(app, 'FileSystemStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    importMigrationFs: true,
  });

  const databaseStack = new DatabaseStack(app, 'DatabaseStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });

  const lambdaStack = new LambdaStack(app, 'LambdaStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    datastoreInstance: databaseStack.datastoreInstance,
    datastoreCredentials: databaseStack.datastoreCredentials,
    vpc: clusterStack.vpc
  })

  const cacheStack = new CacheStack(app, 'CacheStack-test', {
    env: mockEnv,
    environment: 'mock-env',
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
    captchaEnabled: false,
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
    prhToolsInUse: false,
    archiverSendNotificationEmailsToMaintainers: false,
    archiverExemptDomainsFromBrokenLinkNotifications: [],
    cloudstorageEnabled: true,
    sentryTracesSampleRate: "1.0",
    sentryProfilesSampleRate: "1.0"
  });
  // THEN
  const template = Template.fromStack(stack);
  template.hasResource('AWS::ECS::Service', {});
  const taskDefs = template.findResources('AWS::ECS::TaskDefinition', {});
  const containerDefinitions = Object.values(taskDefs).flatMap(taskDef => taskDef.Properties.ContainerDefinitions);
  const environmentVariables = containerDefinitions.flatMap(containerDef => containerDef.Environment).filter(ev => ev !== undefined);
  const analyticsDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'MATOMO_ENABLED' || ev.Value === 'false')
  }, true);
  const captchaDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'CAPTCHA_ENABLED' || ev.Value === 'false')
  }, true);
  expect(analyticsDisabled).toBeFalsy();
  expect(captchaDisabled).toBeTruthy();
  // TODO: write more in-depth resource verification here...
});
