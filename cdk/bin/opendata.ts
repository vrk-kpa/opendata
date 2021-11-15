#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { RegistryStack } from '../lib/registry-stack';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { DrupalStack } from '../lib/drupal-stack';
import { CkanStack } from '../lib/ckan-stack';
import { WebStack } from '../lib/web-stack';

const app = new cdk.App();

const opendataRegistryStack = new RegistryStack(app, 'OpendataRegistryStack', {
  env: {
    account: '156418131626',
    region: 'eu-west-1',
  },
});

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

const databaseStackDev = new DatabaseStack(app, 'DatabaseStack-dev', {
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
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  repositories: {
    'ckan': opendataRegistryStack.ckanRepository,
    'datapusher': opendataRegistryStack.datapusherRepository,
    'solr': opendataRegistryStack.solrRepository,
  },
  vpc: clusterStackDev.vpc,
  cluster: clusterStackDev.cluster,
  namespace: clusterStackDev.namespace,
  fileSystems: {
    'ckan': fileSystemStackDev.ckanFs,
    'solr': fileSystemStackDev.solrFs,
  },
  databaseSecurityGroup: databaseStackDev.databaseSecurityGroup,
  databaseInstance: databaseStackDev.databaseInstance,
  cachePort: cacheStackDev.cachePort,
  cacheSecurityGroup: cacheStackDev.cacheSecurityGroup,
  cacheCluster: cacheStackDev.cacheCluster,
  captchaEnabled: false,
  analyticsEnabled: false,
  cloudStorageEnabled: true,
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
});

const drupalStackDev = new DrupalStack(app, 'DrupalStack-dev', {
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  repositories: {
    'drupal': opendataRegistryStack.drupalRepository,
  },
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
  env: {
    account: devProps.account,
    region: devProps.region,
  },
  environment: devProps.environment,
  fqdn: devProps.fqdn,
  secondaryFqdn: devProps.secondaryFqdn,
  domainName: devProps.domainName,
  secondaryDomainName: devProps.secondaryDomainName,
  repositories: {
    'nginx': opendataRegistryStack.nginxRepository,
  },
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
