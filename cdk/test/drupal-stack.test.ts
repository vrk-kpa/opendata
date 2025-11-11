import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { DrupalStack } from '../lib/drupal-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';
import {BackupStack} from "../lib/backup-stack";

test('verify drupal stack resources', () => {
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
    backupPlan: backupStack.backupPlan
  });

  const databaseStack = new DatabaseStack(app, 'DatabaseStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });
  const cacheStack = new CacheStack(app, 'CacheStack-test', {
    env: mockEnv,
    environment: 'mock-env',
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
    webFqdn: 'localhost',
    vpc: clusterStack.vpc,
    cluster: clusterStack.cluster,
    namespace: clusterStack.namespace,
    fileSystems: {
      'drupal': fileSystemStack.drupalFs,
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
    sentryTracesSampleRate: "1.0"
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

test('create a drupal stack without analytics', () => {
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
    backupPlan: backupStack.backupPlan
  });

  const databaseStack = new DatabaseStack(app, 'DatabaseStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });
  const cacheStack = new CacheStack(app, 'CacheStack-test', {
    env: mockEnv,
    environment: 'mock-env',
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
    webFqdn: 'localhost',
    vpc: clusterStack.vpc,
    cluster: clusterStack.cluster,
    namespace: clusterStack.namespace,
    fileSystems: {
      'drupal': fileSystemStack.drupalFs,
    },
    databaseSecurityGroup: databaseStack.databaseSecurityGroup,
    databaseInstance: databaseStack.databaseInstance,
    cachePort: cacheStack.cachePort,
    cacheSecurityGroup: cacheStack.cacheSecurityGroup,
    cacheCluster: cacheStack.cacheCluster,
    captchaEnabled: true,
    analyticsEnabled: false,
    drupalTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 1,
      taskMaxCapacity: 2,
    },
    sentryTracesSampleRate: "1.0"
  });

  // THEN
  const template = Template.fromStack(stack);
  const taskDefs = template.findResources('AWS::ECS::TaskDefinition', {});
  const containerDefinitions = Object.values(taskDefs).flatMap(taskDef => taskDef.Properties.ContainerDefinitions);
  const environmentVariables = containerDefinitions.flatMap(containerDef => containerDef.Environment);
  const analyticsDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'MATOMO_ENABLED' || ev.Value === 'false')
  }, true);
  expect(analyticsDisabled).toBeTruthy();
});

test('create a drupal stack without captcha', () => {
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
    backupPlan: backupStack.backupPlan
  });

  const databaseStack = new DatabaseStack(app, 'DatabaseStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });
  const cacheStack = new CacheStack(app, 'CacheStack-test', {
    env: mockEnv,
    environment: 'mock-env',
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
    webFqdn: 'localhost',
    vpc: clusterStack.vpc,
    cluster: clusterStack.cluster,
    namespace: clusterStack.namespace,
    fileSystems: {
      'drupal': fileSystemStack.drupalFs,
    },
    databaseSecurityGroup: databaseStack.databaseSecurityGroup,
    databaseInstance: databaseStack.databaseInstance,
    cachePort: cacheStack.cachePort,
    cacheSecurityGroup: cacheStack.cacheSecurityGroup,
    cacheCluster: cacheStack.cacheCluster,
    captchaEnabled: false,
    analyticsEnabled: true,
    drupalTaskDef: {
      taskCpu: 512,
      taskMem: 1024,
      taskMinCapacity: 1,
      taskMaxCapacity: 2,
    },
    sentryTracesSampleRate: "1.0"
  });

  // THEN
  const template = Template.fromStack(stack);
  const taskDefs = template.findResources('AWS::ECS::TaskDefinition', {});
  const containerDefinitions = Object.values(taskDefs).flatMap(taskDef => taskDef.Properties.ContainerDefinitions);
  const environmentVariables = containerDefinitions.flatMap(containerDef => containerDef.Environment);
  const captchaDisabled = environmentVariables.reduce((prev, ev) => {
    return prev && (ev.Name !== 'CAPTCHA_ENABLED' || ev.Value === 'false')
  }, true);
  expect(captchaDisabled).toBeTruthy();
});
