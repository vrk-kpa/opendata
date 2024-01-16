import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';
import {BackupStack} from "../lib/backup-stack";

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
    backups: true,
    backupPlan: backupStack.backupPlan,
    importMigrationFs: true,
  });
  // THEN
  const template = Template.fromStack(stack);
  template.resourceCountIs('AWS::EC2::SecurityGroup', 4);
  template.resourceCountIs('AWS::EFS::MountTarget', 8);
  template.resourceCountIs('AWS::EFS::FileSystem', 4);
});
