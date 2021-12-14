import * as dotenv from 'dotenv';
import { EnvProps, parseEnv } from '../lib/env-props';
import { expect as expectCDK, matchTemplate, MatchStyle, haveResource } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import { ClusterStack } from '../lib/cluster-stack';

// load .env file, shared with docker setup
// mainly for ECR repo and image tag information
dotenv.config({
  path: '../docker/.env',
});

const envProps: EnvProps = {
  // docker
  REGISTRY: parseEnv('REGISTRY'),
  REGISTRY_ARN: parseEnv('REGISTRY_ARN'),
  REPOSITORY: parseEnv('REPOSITORY'),
  // opendata images
  CKAN_IMAGE_TAG: parseEnv('CKAN_IMAGE_TAG'),
  DRUPAL_IMAGE_TAG: parseEnv('DRUPAL_IMAGE_TAG'),
  SOLR_IMAGE_TAG: parseEnv('SOLR_IMAGE_TAG'),
  NGINX_IMAGE_TAG: parseEnv('NGINX_IMAGE_TAG'),
  // 3rd party images
  DATAPUSHER_IMAGE_TAG: parseEnv('DATAPUSHER_IMAGE_TAG'),
};

test('verify cluster stack resources', () => {
  const app = new cdk.App();
  // WHEN
  const stack = new ClusterStack(app, 'ClusterStack-test', {
    envProps: envProps,
    env: {
      account: '1234567890',
      region: 'eu-west-1',
    },
    environment: 'local',
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'local.localhost',
    secondaryDomainName: 'local.localhost',
  });
  // THEN
  expectCDK(stack).to(haveResource('AWS::ECS::Cluster'));
  expectCDK(stack).to(haveResource('AWS::ECS::ClusterCapacityProviderAssociations', {
    CapacityProviders: [
      'FARGATE',
      'FARGATE_SPOT',
    ],
  }));
  expectCDK(stack).to(haveResource('AWS::ServiceDiscovery::PrivateDnsNamespace'));
});
