#!/usr/bin/env node
import 'source-map-support/register';
import * as dotenv from 'dotenv';
import { EnvProps, parseEnv } from '../lib/env-props';
import * as cdk from '@aws-cdk/core';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { LoadBalancerStack } from '../lib/load-balancer-stack';
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
// infratest env
//

const infratestProps = {
  account: '156418131626',
  region: 'eu-west-1',
  environment: 'infratest',
  fqdn: 'betaavoindata.fi',
  secondaryFqdn: 'betaopendata.fi',
  domainName: 'infratest.betaavoindata.fi',
  secondaryDomainName: 'infratest.betaopendata.fi',
};

const clusterStackInfratest = new ClusterStack(app, 'ClusterStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
});

const fileSystemStackInfratest = new FileSystemStack(app, 'FileSystemStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
  vpc: clusterStackInfratest.vpc,
  importMigrationFs: true,
});

const databaseStackInfratest = new DatabaseStack(app, 'DatabaseStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
  vpc: clusterStackInfratest.vpc,
});

const loadBalancerStackInfratest = new LoadBalancerStack(app, 'LoadBalancerStackInfratest-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
  vpc: clusterStackInfratest.vpc,
});

const cacheStackInfratest = new CacheStack(app, 'CacheStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
  vpc: clusterStackInfratest.vpc,
  cacheNodeType: 'cache.t2.micro',
  cacheEngineVersion: '6.x',
  cacheNumNodes: 1,
});

const ckanStackInfratest = new CkanStack(app, 'CkanStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
  vpc: clusterStackInfratest.vpc,
  cluster: clusterStackInfratest.cluster,
  namespace: clusterStackInfratest.namespace,
  fileSystems: {
    'ckan': fileSystemStackInfratest.ckanFs,
    'solr': fileSystemStackInfratest.solrFs,
  },
  migrationFileSystemProps: {
    securityGroup: fileSystemStackInfratest.migrationFsSg!,
    fileSystem: fileSystemStackInfratest.migrationFs!,
  },
  databaseSecurityGroup: databaseStackInfratest.databaseSecurityGroup,
  databaseInstance: databaseStackInfratest.databaseInstance,
  cachePort: cacheStackInfratest.cachePort,
  cacheSecurityGroup: cacheStackInfratest.cacheSecurityGroup,
  cacheCluster: cacheStackInfratest.cacheCluster,
  captchaEnabled: false,
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
  ckanCronEnabled: false,
  archiverSendNotificationEmailsToMaintainers: false,
  archiverExemptDomainsFromBrokenLinkNotifications: [],
  cloudstorageEnabled: true,
});

const drupalStackInfratest = new DrupalStack(app, 'DrupalStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
  vpc: clusterStackInfratest.vpc,
  cluster: clusterStackInfratest.cluster,
  namespace: clusterStackInfratest.namespace,
  fileSystems: {
    'drupal': fileSystemStackInfratest.drupalFs,
  },
  databaseSecurityGroup: databaseStackInfratest.databaseSecurityGroup,
  databaseInstance: databaseStackInfratest.databaseInstance,
  cachePort: cacheStackInfratest.cachePort,
  cacheSecurityGroup: cacheStackInfratest.cacheSecurityGroup,
  cacheCluster: cacheStackInfratest.cacheCluster,
  captchaEnabled: false,
  analyticsEnabled: false,
  drupalTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 1,
    taskMaxCapacity: 2,
  },
});

const webStackInfratest = new WebStack(app, 'WebStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName,
  vpc: clusterStackInfratest.vpc,
  cluster: clusterStackInfratest.cluster,
  namespace: clusterStackInfratest.namespace,
  fileSystems: {
    'drupal': fileSystemStackInfratest.drupalFs,
    'ckan': fileSystemStackInfratest.ckanFs,
  },
  databaseSecurityGroup: databaseStackInfratest.databaseSecurityGroup,
  databaseInstance: databaseStackInfratest.databaseInstance,
  cachePort: cacheStackInfratest.cachePort,
  cacheSecurityGroup: cacheStackInfratest.cacheSecurityGroup,
  cacheCluster: cacheStackInfratest.cacheCluster,
  loadBalancerCert: loadBalancerStackInfratest.loadBalancerCert,
  loadBalancer: loadBalancerStackInfratest.loadBalancer,
  nginxTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 2,
    taskMaxCapacity: 2,
  },
  drupalService: drupalStackInfratest.drupalService,
  ckanService: ckanStackInfratest.ckanService,
});
