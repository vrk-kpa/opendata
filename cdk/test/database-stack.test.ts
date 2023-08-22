import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { DatabaseStack } from '../lib/database-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';
import {BackupStack} from "../lib/backup-stack";

test('verify database stack resources', () => {
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
  const stack = new DatabaseStack(app, 'DatabaseStack-test', {
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
  // THEN
  // no actual resources to verify
});
