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
import {CertificateStack} from "../lib/certificate-stack";
import {MonitoringStack} from "../lib/monitoring-stack";
import {LambdaStack} from "../lib/lambda-stack";
import {DomainStack} from "../lib/domain-stack";
import {CiTestStack} from "../lib/ci-test-stack";
import {SubDomainStack} from "../lib/sub-domain-stack";
import {ShieldStack} from "../lib/shield-stack";
import {ShieldParameterStack} from "../lib/shield-parameter-stack";
import { ClamavScannerStack } from '../lib/clamav-scanner-stack';
import { DnssecStack } from '../lib/dnssec-stack';
import { DnssecKeyStack } from '../lib/dnssec-key-stack';

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
  CLAMAV_IMAGE_TAG: parseEnv('CLAMAV_IMAGE_TAG'),
  // 3rd party images
  FUSEKI_IMAGE_TAG: parseEnv('FUSEKI_IMAGE_TAG'),
};


//
// beta env
//

const betaProps = {
  account: '156418131626',
  region: 'eu-west-1',
  environment: 'beta',
  fqdn: 'betaavoindata.fi',
  secondaryFqdn: 'betaopendata.fi',
  tertiaryFqdn: null,
  domainName: 'www.betaavoindata.fi',
  secondaryDomainName: 'www.betaopendata.fi',
  dnssecKeyAlias: 'dnssec-key-beta',
};

const clusterStackBeta = new ClusterStack(app, 'ClusterStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  vpcId: 'vpc-0162f60213eb96ab2'
});

const backupStackBeta = new BackupStack(app, 'BackupStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  backups: true,
  importVault: true
})


const fileSystemStackBeta = new FileSystemStack(app, 'FileSystemStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  vpc: clusterStackBeta.vpc,
  backups: true,
  backupPlan: backupStackBeta.backupPlan
});

const databaseStackBeta = new DatabaseStack(app, 'DatabaseStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  vpc: clusterStackBeta.vpc,
  backups: true,
  backupPlan: backupStackBeta.backupPlan,
  multiAz: false
});

const lambdaStackBeta = new LambdaStack(app, 'LambdaStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  datastoreInstance: databaseStackBeta.datastoreInstance,
  datastoreCredentials: databaseStackBeta.datastoreCredentials,
  vpc: clusterStackBeta.vpc
})




const loadBalancerStackBeta = new LoadBalancerStack(app, 'LoadBalancerStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  vpc: clusterStackBeta.vpc,
  domainName: betaProps.domainName,
  fqdn: betaProps.fqdn,
  secondaryDomainName: betaProps.secondaryDomainName,
  secondaryFqdn: betaProps.secondaryFqdn
});


const certificateStackBeta = new CertificateStack(app, 'CertificateStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  vpc: clusterStackBeta.vpc,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
  domainName: betaProps.domainName,
  secondaryDomainName: betaProps.secondaryDomainName,
  zone: loadBalancerStackBeta.zone,
  alternativeZone: loadBalancerStackBeta.alternativeZone
})


const shieldParameterStackBeta = new ShieldParameterStack(app, 'ShieldParameterStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region
  },
  environment: betaProps.environment,
})

const shieldStackBeta = new ShieldStack(app, 'ShieldStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  bannedIpsRequestSamplingEnabled: false,
  highPriorityRequestSamplingEnabled: false,
  rateLimitRequestSamplingEnabled: false,
  requestSampleAllTrafficEnabled: false,
  bannedIpListParameterName: shieldParameterStackBeta.bannedIpListParameterName,
  whitelistedIpListParameterName: shieldParameterStackBeta.whitelistedIpListParameterName,
  highPriorityCountryCodeListParameterName: shieldParameterStackBeta.highPriorityCountryCodeListParameterName,
  highPriorityRateLimit: shieldParameterStackBeta.highPriorityRateLimit,
  rateLimit: shieldParameterStackBeta.rateLimit,
  managedRulesParameterName: shieldParameterStackBeta.managedRulesParameterName,
  snsTopicArn: shieldParameterStackBeta.snsTopicArn,
  wafAutomationArn: shieldParameterStackBeta.wafAutomationArn,
  evaluationPeriod: shieldParameterStackBeta.evaluationPeriod,
  loadBalancer: loadBalancerStackBeta.loadBalancer,
  blockedUserAgentsParameterName: shieldParameterStackBeta.blockedUserAgentsParameterName
})

const cacheStackBeta = new CacheStack(app, 'CacheStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
  vpc: clusterStackBeta.vpc,
  cacheNodeType: 'cache.t3.small',
  cacheEngineVersion: '7.1',
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
  databaseSecurityGroup: databaseStackBeta.databaseSecurityGroup,
  databaseInstance: databaseStackBeta.databaseInstance,
  datastoreInstance: databaseStackBeta.datastoreInstance,
  datastoreCredentials: databaseStackBeta.datastoreCredentials,
  datastoreJobsCredentials: lambdaStackBeta.datastoreJobsCredentials,
  datastoreReadCredentials: lambdaStackBeta.datastoreReadCredentials,
  datastoreUserCredentials: lambdaStackBeta.datastoreUserCredentials,
  datastoreSecurityGroup: databaseStackBeta.datastoreSecurityGroup,
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
    taskMinCapacity: 1,
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
  ckanUwsgiProps: {
    processes: 2,
    threads: 2
  },
  ckanCronEnabled: true,
  archiverSendNotificationEmailsToMaintainers: false,
  archiverExemptDomainsFromBrokenLinkNotifications: [],
  cloudstorageEnabled: true,
  sentryTracesSampleRate: "1.0",
  sentryProfilesSampleRate: "1.0"
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
  sentryTracesSampleRate: "1.0"
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
  certificate: certificateStackBeta.certificate,
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

const monitoringStackBeta = new MonitoringStack(app, 'MonitoringStack-beta', {
  sendToZulipTopic: lambdaStackBeta.sendToZulipTopic,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  environment: betaProps.environment,
});
const clamavScannerStackBeta = new ClamavScannerStack(app, 'ClamavScannerStack-beta', {
  environment: betaProps.environment,
  envProps: envProps,
  env: {
    account: betaProps.account,
    region: betaProps.region,
  },
  clamavTaskDef: {
    taskCpu: 512,
    taskMem: 3072,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  cluster: clusterStackBeta.cluster,
  topic: lambdaStackBeta.sendToZulipTopic,
  datasetBucketName: 'avoindata-beta-datasets',
  clamavFileSystem: fileSystemStackBeta.clamavFs,
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
  tertiaryFqdn: "yhteentoimivuus.fi",
  domainName: 'www.avoindata.fi',
  secondaryDomainName: 'www.opendata.fi',
  newDomainName: "avoindata.suomi.fi",
  dnssecKeyAlias: 'dnssec-key-prod',
};

const clusterStackProd = new ClusterStack(app, 'ClusterStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  vpcId: 'vpc-07f19c5db1390f949'
});

const backupStackProd = new BackupStack(app, 'BackupStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  backups: true,
  importVault: false
})

const fileSystemStackProd = new FileSystemStack(app, 'FileSystemStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  vpc: clusterStackProd.vpc,
  backups: true,
  backupPlan: backupStackProd.backupPlan
});

const databaseStackProd = new DatabaseStack(app, 'DatabaseStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  vpc: clusterStackProd.vpc,
  backups: true,
  backupPlan: backupStackProd.backupPlan,
  multiAz: true
});

const lambdaStackProd = new LambdaStack(app, 'LambdaStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  datastoreInstance: databaseStackProd.datastoreInstance,
  datastoreCredentials: databaseStackProd.datastoreCredentials,
  vpc: clusterStackProd.vpc
})


const loadBalancerStackProd = new LoadBalancerStack(app, 'LoadBalancerStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  vpc: clusterStackProd.vpc,
  domainName: prodProps.domainName,
  fqdn: prodProps.fqdn,
  secondaryDomainName: prodProps.secondaryDomainName,
  secondaryFqdn: prodProps.secondaryFqdn
});


const certificateStackProd = new CertificateStack(app, 'CertificateStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region
  },
  environment: prodProps.environment,
  vpc: clusterStackProd.vpc,
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  domainName: prodProps.domainName,
  secondaryDomainName: prodProps.secondaryDomainName,
  zone: loadBalancerStackProd.zone,
  alternativeZone: loadBalancerStackProd.alternativeZone
})

const shieldParameterStackProd = new ShieldParameterStack(app, 'ShieldParameterStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region
  },
  environment: prodProps.environment,
})

const shieldStackProd = new ShieldStack(app, 'ShieldStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region
  },
  environment: prodProps.environment,
  bannedIpsRequestSamplingEnabled: false,
  highPriorityRequestSamplingEnabled: false,
  rateLimitRequestSamplingEnabled: false,
  requestSampleAllTrafficEnabled: false,
  bannedIpListParameterName: shieldParameterStackProd.bannedIpListParameterName,
  whitelistedIpListParameterName: shieldParameterStackProd.whitelistedIpListParameterName,
  highPriorityCountryCodeListParameterName: shieldParameterStackProd.highPriorityCountryCodeListParameterName,
  highPriorityRateLimit: shieldParameterStackProd.highPriorityRateLimit,
  rateLimit: shieldParameterStackProd.rateLimit,
  managedRulesParameterName: shieldParameterStackProd.managedRulesParameterName,
  snsTopicArn: shieldParameterStackProd.snsTopicArn,
  wafAutomationArn: shieldParameterStackProd.wafAutomationArn,
  evaluationPeriod: shieldParameterStackProd.evaluationPeriod,
  loadBalancer: loadBalancerStackProd.loadBalancer,
  blockedUserAgentsParameterName: shieldParameterStackProd.blockedUserAgentsParameterName
})

const cacheStackProd = new CacheStack(app, 'CacheStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
  vpc: clusterStackProd.vpc,
  cacheNodeType: 'cache.t3.small',
  cacheEngineVersion: '7.1',
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
  databaseSecurityGroup: databaseStackProd.databaseSecurityGroup,
  databaseInstance: databaseStackProd.databaseInstance,
  datastoreInstance: databaseStackProd.datastoreInstance,
  datastoreCredentials: databaseStackProd.datastoreCredentials,
  datastoreJobsCredentials: lambdaStackProd.datastoreJobsCredentials,
  datastoreReadCredentials: lambdaStackProd.datastoreReadCredentials,
  datastoreUserCredentials: lambdaStackProd.datastoreUserCredentials,
  datastoreSecurityGroup: databaseStackProd.datastoreSecurityGroup,
  cachePort: cacheStackProd.cachePort,
  cacheSecurityGroup: cacheStackProd.cacheSecurityGroup,
  cacheCluster: cacheStackProd.cacheCluster,
  captchaEnabled: true,
  analyticsEnabled: true,
  ckanTaskDef: {
    taskCpu: 2048,
    taskMem: 4096,
    taskMinCapacity: 3,
    taskMaxCapacity: 6,
  },
  ckanCronTaskDef: {
    taskCpu: 4096,
    taskMem: 8192,
    taskMinCapacity: 1,
    taskMaxCapacity: 1,
  },
  datapusherTaskDef: {
    taskCpu: 1024,
    taskMem: 8192,
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
  ckanUwsgiProps: {
    processes: 8,
    threads: 2
  },
  ckanCronEnabled: true,
  archiverSendNotificationEmailsToMaintainers: true,
  archiverExemptDomainsFromBrokenLinkNotifications: ['fmi.fi'],
  cloudstorageEnabled: true,
  sentryTracesSampleRate: "0.1",
  sentryProfilesSampleRate: "0.1"
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
  sentryTracesSampleRate: "0.1"
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
  certificate: certificateStackProd.certificate,
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

const monitoringStackProd = new MonitoringStack(app, 'MonitoringStack-prod', {
  sendToZulipTopic: lambdaStackProd.sendToZulipTopic,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  environment: prodProps.environment,
});

const domainStackProd = new DomainStack(app, 'DomainStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  fqdn: prodProps.fqdn,
  secondaryFqdn: prodProps.secondaryFqdn,
  tertiaryFqdn: prodProps.tertiaryFqdn,
  zoneName: prodProps.newDomainName,
  crossAccountId: betaProps.account
})

const dnssecKeyStackProd = new DnssecKeyStack(app, 'DnssecKeyStack-prod', {
  env: {
    account: prodProps.account,
    region: 'us-east-1'
  },
  keyAlias: prodProps.dnssecKeyAlias
})

const dnssecStackProd = new DnssecStack(app, 'DnssecStack-prod', {
  env: {
    account: prodProps.account,
    region: prodProps.region
  },
  zones: domainStackProd.zones,
  keyAlias: prodProps.dnssecKeyAlias
})

const subDomainStackBeta = new SubDomainStack(app, 'SubDomainStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region
  },
  prodAccountId: prodProps.account,
  subDomainName: betaProps.environment,
  fqdn: betaProps.fqdn,
  secondaryFqdn: betaProps.secondaryFqdn,
})

const dnssecKeyStackBeta = new DnssecKeyStack(app, 'DnssecKeyStack-beta', {
  env: {
    account: betaProps.account,
    region: 'us-east-1'
  },
  keyAlias: betaProps.dnssecKeyAlias
})

const dnssecStackBeta = new DnssecStack(app, 'DnssecStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region
  },
  zones: subDomainStackBeta.zones,
  keyAlias: betaProps.dnssecKeyAlias
})

const ciTestStackBeta = new CiTestStack(app, 'CiTestStack-beta', {
  env: {
    account: betaProps.account,
    region: betaProps.region
  },
  githubOrg: "vrk-kpa",
  githubRepo: "opendata",
  githubRepo2: "ckanext-cloudstorage",
  testBucketName: "avoindata-ci-test-bucket"
})

const clamavScannerStackProd = new ClamavScannerStack(app, 'ClamavScannerStack-prod', {
  environment: prodProps.environment,
  envProps: envProps,
  env: {
    account: prodProps.account,
    region: prodProps.region,
  },
  clamavTaskDef: {
    taskCpu: 512,
    taskMem: 1024,
    taskMinCapacity: 0,
    taskMaxCapacity: 1,
  },
  cluster: clusterStackProd.cluster,
  topic: lambdaStackProd.sendToZulipTopic,
  datasetBucketName: 'avoindata-prod-datasets',
  clamavFileSystem: fileSystemStackProd.clamavFs,
});
