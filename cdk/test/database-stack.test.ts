import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { DatabaseStack } from '../lib/database-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';
import {BackupStack} from "../lib/backup-stack";

test('verify database stack resources', () => {
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
  const stack = new DatabaseStack(app, 'DatabaseStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    backups: true,
    backupPlan: backupStack.backupPlan,
    multiAz: true
  });
  // THEN
  // no actual resources to verify
});
