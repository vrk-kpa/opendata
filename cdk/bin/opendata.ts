#!/usr/bin/env node
import 'source-map-support/register';
import * as dotenv from 'dotenv';
import { EnvProps, parseEnv } from '../lib/env-props';
import * as cdk from 'aws-cdk-lib';
import { DatabaseStack } from '../lib/database-stack';
import { CacheStack } from '../lib/cache-stack';
import { LoadBalancerStack } from '../lib/load-balancer-stack';
import { ClusterStack } from '../lib/cluster-stack';
import { FileSystemStack } from '../lib/filesystem-stack';
import { DrupalStack } from '../lib/drupal-stack';
import { CkanStack } from '../lib/ckan-stack';
import { WebStack } from '../lib/web-stack';
import { BackupStack } from "../lib/backup-stack"
import {BypassCdnStack} from "../lib/bypass-cdn-stack";
import {CertificateStack} from "../lib/certificate-stack";

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
  DATAPUSHER_IMAGE_TAG: parseEnv('DATAPUSHER_IMAGE_TAG'),
  NGINX_IMAGE_TAG: parseEnv('NGINX_IMAGE_TAG'),
  // 3rd party images
  FUSEKI_IMAGE_TAG: parseEnv('FUSEKI_IMAGE_TAG'),
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

const backupStackInfratest = new BackupStack(app, 'BackupStack-infratest', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  domainName: infratestProps.domainName,
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryDomainName: infratestProps.secondaryDomainName,
  secondaryFqdn: infratestProps.secondaryFqdn,
  backups: false,
  importVault: false
})

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
  backups: false,
  backupPlan: backupStackInfratest.backupPlan,
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
  backups: false,
  backupPlan: backupStackInfratest.backupPlan
});

const certificateStackInfratest = new CertificateStack(app, 'CertificateStack-infra', {
  envProps: envProps,
  env: {
    account: infratestProps.account,
    region: infratestProps.region,
  },
  environment: infratestProps.environment,
  fqdn: infratestProps.fqdn,
  secondaryFqdn: infratestProps.secondaryFqdn,
  domainName: infratestProps.domainName,
  secondaryDomainName: infratestProps.secondaryDomainName
})

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
  cert: certificateStackInfratest.certificate
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
  cacheNodeType: 'cache.t3.small',
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
    'fuseki': fileSystemStackInfratest.fusekiFs,
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
  fusekiTaskDef: {
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
    taskMinCapacity: 1,
    taskMaxCapacity: 2,
  },
  drupalService: drupalStackInfratest.drupalService,
  ckanService: ckanStackInfratest.ckanService,
  allowRobots: 'false',
});

//
// beta env
//

const betaProps = {
  account: '156418131626',
  region: 'eu-west-1',
  environment: 'beta',
  fqdn: 'betaavoindata.fi',
  secondaryFqdn: 'betaopendata.fi',
  domainName: 'www.betaavoindata.fi',
  secondaryDomainName: 'www.betaopendata.fi',
};

const clusterStackBeta = new ClusterStack(app, 'ClusterStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
});

const backupStackBeta = new BackupStack(app, 'BackupStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  domainName: betaProps.domainName,
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryDomainName: betaProps.secondaryDomainName,
  secondaryFqdn: betaProps.secondaryFqdn,
  backups: true,
  importVault: true
})


const fileSystemStackBeta = new FileSystemStack(app, 'FileSystemStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  vpc: clusterStackBeta.vpc,
  backups: true,
  backupPlan: backupStackBeta.backupPlan,
  importMigrationFs: true,
});

const databaseStackBeta = new DatabaseStack(app, 'DatabaseStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  vpc: clusterStackBeta.vpc,
  backups: true,
  backupPlan: backupStackBeta.backupPlan
});

const certificateStackBeta = new CertificateStack(app, 'CertificateStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName
})

const loadBalancerStackBeta = new LoadBalancerStack(app, 'LoadBalancerStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  vpc: clusterStackBeta.vpc,
  cert: certificateStackBeta.certificate
});

const cacheStackBeta = new CacheStack(app, 'CacheStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  vpc: clusterStackBeta.vpc,
  cacheNodeType: 'cache.t3.small',
  cacheEngineVersion: '6.x',
  cacheNumNodes: 1,
});

const ckanStackBeta = new CkanStack(app, 'CkanStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  vpc: clusterStackBeta.vpc,
  cluster: clusterStackBeta.cluster,
  namespace: clusterStackBeta.namespace,
  fileSystems: {
    'ckan': fileSystemStackBeta.ckanFs,
    'solr': fileSystemStackBeta.solrFs,
    'fuseki': fileSystemStackBeta.fusekiFs,
  },
  migrationFileSystemProps: {
    securityGroup: fileSystemStackBeta.migrationFsSg!,
    fileSystem: fileSystemStackBeta.migrationFs!,
  },
  databaseSecurityGroup: databaseStackBeta.databaseSecurityGroup,
  databaseInstance: databaseStackBeta.databaseInstance,
  cachePort: cacheStackBeta.cachePort,
  cacheSecurityGroup: cacheStackBeta.cacheSecurityGroup,
  cacheCluster: cacheStackBeta.cacheCluster,
  captchaEnabled: true,
  analyticsEnabled: true,
  ckanTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 1,
    taskMaxCapacity: 3,
  },
  ckanCronTaskDef: {
    taskCpu: 1024,
    taskMem: 4096,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  datapusherTaskDef: {
    taskCpu: 512,
    taskMem: 2048,
    taskMinCapacity: 1,
    taskMaxCapacity: 3,
  },
  solrTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  fusekiTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  ckanCronEnabled: true,
  archiverSendNotificationEmailsToMaintainers: false,
  archiverExemptDomainsFromBrokenLinkNotifications: [],
  cloudstorageEnabled: true,
});

const drupalStackBeta = new DrupalStack(app, 'DrupalStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  vpc: clusterStackBeta.vpc,
  cluster: clusterStackBeta.cluster,
  namespace: clusterStackBeta.namespace,
  fileSystems: {
    'drupal': fileSystemStackBeta.drupalFs,
  },
  migrationFileSystemProps: {
    securityGroup: fileSystemStackBeta.migrationFsSg!,
    fileSystem: fileSystemStackBeta.migrationFs!,
  },
  databaseSecurityGroup: databaseStackBeta.databaseSecurityGroup,
  databaseInstance: databaseStackBeta.databaseInstance,
  cachePort: cacheStackBeta.cachePort,
  cacheSecurityGroup: cacheStackBeta.cacheSecurityGroup,
  cacheCluster: cacheStackBeta.cacheCluster,
  captchaEnabled: true,
  analyticsEnabled: true,
  drupalTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 1,
    taskMaxCapacity: 3,
  },
});

const webStackBeta = new WebStack(app, 'WebStack-beta', {
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  vpc: clusterStackBeta.vpc,
  cluster: clusterStackBeta.cluster,
  namespace: clusterStackBeta.namespace,
  fileSystems: {
    'drupal': fileSystemStackBeta.drupalFs,
  },
  databaseSecurityGroup: databaseStackBeta.databaseSecurityGroup,
  databaseInstance: databaseStackBeta.databaseInstance,
  cachePort: cacheStackBeta.cachePort,
  cacheSecurityGroup: cacheStackBeta.cacheSecurityGroup,
  cacheCluster: cacheStackBeta.cacheCluster,
  loadBalancerCert: loadBalancerStackBeta.loadBalancerCert,
  loadBalancer: loadBalancerStackBeta.loadBalancer,
  nginxTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 2,
    taskMaxCapacity: 4,
  },
  drupalService: drupalStackBeta.drupalService,
  ckanService: ckanStackBeta.ckanService,
  allowRobots: 'false',
});

//
// prod env
//

const prodProps = {
  account: '903124270034',
  region: 'eu-west-1',
  environment: 'prod',
  fqdn: 'avoindata.fi',
  secondaryFqdn: 'opendata.fi',
  domainName: 'www.avoindata.fi',
  secondaryDomainName: 'www.opendata.fi',
};

const clusterStackProd = new ClusterStack(app, 'ClusterStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
});

const backupStackProd = new BackupStack(app, 'BackupStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  domainName: prodProps.domainName,
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryDomainName: prodProps.secondaryDomainName,
  secondaryFqdn: prodProps.secondaryFqdn,
  backups: true,
  importVault: false
})

const fileSystemStackProd = new FileSystemStack(app, 'FileSystemStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  vpc: clusterStackProd.vpc,
  backups: true,
  backupPlan: backupStackProd.backupPlan,
  importMigrationFs: true,
});

const databaseStackProd = new DatabaseStack(app, 'DatabaseStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  vpc: clusterStackProd.vpc,
  backups: true,
  backupPlan: backupStackProd.backupPlan
});

const certificateStackProd = new CertificateStack(app, 'CertificateStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName
})

const loadBalancerStackProd = new LoadBalancerStack(app, 'LoadBalancerStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  vpc: clusterStackProd.vpc,
  cert: certificateStackProd.certificate
});

const cacheStackProd = new CacheStack(app, 'CacheStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  vpc: clusterStackProd.vpc,
  cacheNodeType: 'cache.t3.small',
  cacheEngineVersion: '6.x',
  cacheNumNodes: 1,
});

const ckanStackProd = new CkanStack(app, 'CkanStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  vpc: clusterStackProd.vpc,
  cluster: clusterStackProd.cluster,
  namespace: clusterStackProd.namespace,
  fileSystems: {
    'ckan': fileSystemStackProd.ckanFs,
    'solr': fileSystemStackProd.solrFs,
    'fuseki': fileSystemStackProd.fusekiFs,
  },
  migrationFileSystemProps: {
    securityGroup: fileSystemStackProd.migrationFsSg!,
    fileSystem: fileSystemStackProd.migrationFs!,
  },
  databaseSecurityGroup: databaseStackProd.databaseSecurityGroup,
  databaseInstance: databaseStackProd.databaseInstance,
  cachePort: cacheStackProd.cachePort,
  cacheSecurityGroup: cacheStackProd.cacheSecurityGroup,
  cacheCluster: cacheStackProd.cacheCluster,
  captchaEnabled: true,
  analyticsEnabled: true,
  ckanTaskDef: {
    taskCpu: 2048,
    taskMem: 4096,
    taskMinCapacity: 2,
    taskMaxCapacity: 4,
  },
  ckanCronTaskDef: {
    taskCpu: 1024,
    taskMem: 4096,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  datapusherTaskDef: {
    taskCpu: 512,
    taskMem: 2048,
    taskMinCapacity: 1,
    taskMaxCapacity: 4,
  },
  solrTaskDef: {
    taskCpu: 1024,
    taskMem: 2048,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  fusekiTaskDef: {
    taskCpu: 1024,
    taskMem: 2048,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  ckanCronEnabled: true,
  archiverSendNotificationEmailsToMaintainers: true,
  archiverExemptDomainsFromBrokenLinkNotifications: ['fmi.fi'],
  cloudstorageEnabled: true,
});

const drupalStackProd = new DrupalStack(app, 'DrupalStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  vpc: clusterStackProd.vpc,
  cluster: clusterStackProd.cluster,
  namespace: clusterStackProd.namespace,
  fileSystems: {
    'drupal': fileSystemStackProd.drupalFs,
  },
  migrationFileSystemProps: {
    securityGroup: fileSystemStackProd.migrationFsSg!,
    fileSystem: fileSystemStackProd.migrationFs!,
  },
  databaseSecurityGroup: databaseStackProd.databaseSecurityGroup,
  databaseInstance: databaseStackProd.databaseInstance,
  cachePort: cacheStackProd.cachePort,
  cacheSecurityGroup: cacheStackProd.cacheSecurityGroup,
  cacheCluster: cacheStackProd.cacheCluster,
  captchaEnabled: true,
  analyticsEnabled: true,
  drupalTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 2,
    taskMaxCapacity: 4,
  },
});

const webStackProd = new WebStack(app, 'WebStack-prod', {
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  vpc: clusterStackProd.vpc,
  cluster: clusterStackProd.cluster,
  namespace: clusterStackProd.namespace,
  fileSystems: {
    'drupal': fileSystemStackProd.drupalFs,
  },
  databaseSecurityGroup: databaseStackProd.databaseSecurityGroup,
  databaseInstance: databaseStackProd.databaseInstance,
  cachePort: cacheStackProd.cachePort,
  cacheSecurityGroup: cacheStackProd.cacheSecurityGroup,
  cacheCluster: cacheStackProd.cacheCluster,
  loadBalancerCert: loadBalancerStackProd.loadBalancerCert,
  loadBalancer: loadBalancerStackProd.loadBalancer,
  nginxTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 2,
    taskMaxCapacity: 6,
  },
  drupalService: drupalStackProd.drupalService,
  ckanService: ckanStackProd.ckanService,
  allowRobots: 'true',
});
