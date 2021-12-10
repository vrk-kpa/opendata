#!/usr/bin/env node
import 'source-map-support/register';
import * as dotenv from 'dotenv';
import { EnvProps, parseEnv } from '../lib/env-props';
import * as cdk from '@aws-cdk/core';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { DrupalStack } from '../lib/drupal-stack';
import { CkanStack } from '../lib/ckan-stack';
import { WebStack } from '../lib/web-stack';

// load .env file, shared with docker setup
// mainly for ECR repo and image tag information
dotenv.config({
  path: '../docker/.env',
});

const app = new cdk.App();

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

//
// dev env
//

const devProps = {
  account: '156418131626',
  region: 'eu-west-1',
  environment: 'dev',
  fqdn: 'betaavoindata.fi',
  secondaryFqdn: 'betaopendata.fi',
  domainName: 'dev.betaavoindata.fi',
  secondaryDomainName: 'dev.betaopendata.fi',
};

const clusterStackDev = new ClusterStack(app, 'ClusterStack-dev', {
  envProps: envProps,
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
});

const fileSystemStackDev = new FileSystemStack(app, 'FileSystemStack-dev', {
  envProps: envProps,
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  vpc: clusterStackDev.vpc,
  importMigrationFs: true,
});

const databaseStackDev = new DatabaseStack(app, 'DatabaseStack-dev', {
  envProps: envProps,
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  vpc: clusterStackDev.vpc,
});

const cacheStackDev = new CacheStack(app, 'CacheStack-dev', {
  envProps: envProps,
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  vpc: clusterStackDev.vpc,
  cacheNodeType: 'cache.t2.micro',
  cacheEngineVersion: '6.x',
  cacheNumNodes: 1,
});

const ckanStackDev = new CkanStack(app, 'CkanStack-dev', {
  envProps: envProps,
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  vpc: clusterStackDev.vpc,
  cluster: clusterStackDev.cluster,
  namespace: clusterStackDev.namespace,
  fileSystems: {
    'ckan': fileSystemStackDev.ckanFs,
    'solr': fileSystemStackDev.solrFs,
  },
  migrationFileSystemProps: {
    securityGroup: fileSystemStackDev.migrationFsSg!,
    fileSystem: fileSystemStackDev.migrationFs!,
  },
  databaseSecurityGroup: databaseStackDev.databaseSecurityGroup,
  databaseInstance: databaseStackDev.databaseInstance,
  cachePort: cacheStackDev.cachePort,
  cacheSecurityGroup: cacheStackDev.cacheSecurityGroup,
  cacheCluster: cacheStackDev.cacheCluster,
  captchaEnabled: false,
  analyticsEnabled: false,
  ckanTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
  },
  ckanCronTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
  },
  datapusherTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
  },
  solrTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
  },
  ckanCronEnabled: false,
  archiverSendNotificationEmailsToMaintainers: false,
  archiverExemptDomainsFromBrokenLinkNotifications: [],
  cloudstorageEnabled: true,
});

const drupalStackDev = new DrupalStack(app, 'DrupalStack-dev', {
  envProps: envProps,
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  vpc: clusterStackDev.vpc,
  cluster: clusterStackDev.cluster,
  namespace: clusterStackDev.namespace,
  fileSystems: {
    'drupal': fileSystemStackDev.drupalFs,
  },
  databaseSecurityGroup: databaseStackDev.databaseSecurityGroup,
  databaseInstance: databaseStackDev.databaseInstance,
  cachePort: cacheStackDev.cachePort,
  cacheSecurityGroup: cacheStackDev.cacheSecurityGroup,
  cacheCluster: cacheStackDev.cacheCluster,
  captchaEnabled: false,
  analyticsEnabled: false,
  drupalTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
  },
});

const webStackDev = new WebStack(app, 'WebStack-dev', {
  envProps: envProps,
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  vpc: clusterStackDev.vpc,
  cluster: clusterStackDev.cluster,
  namespace: clusterStackDev.namespace,
  fileSystems: {
    'drupal': fileSystemStackDev.drupalFs,
    'ckan': fileSystemStackDev.ckanFs,
  },
  databaseSecurityGroup: databaseStackDev.databaseSecurityGroup,
  databaseInstance: databaseStackDev.databaseInstance,
  cachePort: cacheStackDev.cachePort,
  cacheSecurityGroup: cacheStackDev.cacheSecurityGroup,
  cacheCluster: cacheStackDev.cacheCluster,
  nginxTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
  },
  drupalService: drupalStackDev.drupalService,
  ckanService: ckanStackDev.ckanService,
});
