import { expect as expectCDK, matchTemplate, MatchStyle, haveResource } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import { RegistryStack } from '../lib/registry-stack';

test('verify registry stack resources', () => {
    const app = new cdk.App();
    // WHEN
    const stack = new RegistryStack(app, 'RegistryStack-test');
    // THEN
    expectCDK(stack).to(haveResource('AWS::ECR::Repository', {
      RepositoryName: 'opendata/nginx',
      ImageScanningConfiguration: {
        ScanOnPush: true,
      },
      ImageTagMutability: 'MUTABLE',
    }));
    expectCDK(stack).to(haveResource('AWS::ECR::Repository', {
      RepositoryName: 'opendata/drupal',
      ImageScanningConfiguration: {
        ScanOnPush: true,
      },
      ImageTagMutability: 'MUTABLE',
    }));
    expectCDK(stack).to(haveResource('AWS::ECR::Repository', {
      RepositoryName: 'opendata/ckan',
      ImageScanningConfiguration: {
        ScanOnPush: true,
      },
      ImageTagMutability: 'MUTABLE',
    }));
    expectCDK(stack).to(haveResource('AWS::ECR::Repository', {
      RepositoryName: 'opendata/datapusher',
      ImageScanningConfiguration: {
        ScanOnPush: true,
      },
      ImageTagMutability: 'MUTABLE',
    }));
    expectCDK(stack).to(haveResource('AWS::ECR::Repository', {
      RepositoryName: 'opendata/solr',
      ImageScanningConfiguration: {
        ScanOnPush: true,
      },
      ImageTagMutability: 'MUTABLE',
    }));
});
