import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';
import {BackupStack} from "../lib/backup-stack";

test('verify filesystem stack resources', () => {
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

  // WHEN
  const stack = new FileSystemStack(app, 'FileSystemStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan
  });
  // THEN
  const template = Template.fromStack(stack);
  template.resourceCountIs('AWS::EC2::SecurityGroup', 5);
  template.resourceCountIs('AWS::EFS::MountTarget', 10);
  template.resourceCountIs('AWS::EFS::FileSystem', 5);
});
