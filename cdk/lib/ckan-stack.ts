import * as cdk from '@aws-cdk/core';
import * as iam from '@aws-cdk/aws-iam';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';
import * as elb from '@aws-cdk/aws-elasticloadbalancingv2';
import * as ecsp from '@aws-cdk/aws-ecs-patterns';
import * as ssm from '@aws-cdk/aws-ssm';
import * as sm from '@aws-cdk/aws-secretsmanager';
import * as efs from '@aws-cdk/aws-efs';
import * as logs from '@aws-cdk/aws-logs';

import { CkanStackProps } from './ckan-stack-props';

export class CkanStack extends cdk.Stack {
  readonly ckanFsDataAccessPoint: efs.IAccessPoint;
  readonly ckanFsResourcesAccessPoint: efs.IAccessPoint;
  readonly solrFsDataAccessPoint: efs.IAccessPoint;
  readonly ckanService: ecs.FargateService;

  constructor(scope: cdk.Construct, id: string, props: CkanStackProps) {
    super(scope, id, props);

    // get params
    const pCkanImageVersion = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanImageVersion', {
      parameterName: `/${props.environment}/opendata/ckan/image_version`,
    });
    const pDatapusherImageVersion = ssm.StringParameter.fromStringParameterAttributes(this, 'pDatapusherImageVersion', {
      parameterName: `/${props.environment}/opendata/datapusher/image_version`,
    });
    const pSolrImageVersion = ssm.StringParameter.fromStringParameterAttributes(this, 'pSolrImageVersion', {
      parameterName: `/${props.environment}/opendata/solr/image_version`,
    });
    const pDbHost = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbHost', {
      parameterName: `/${props.environment}/opendata/common/db_host`,
    });
    const pDbCkan = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbCkan', {
      parameterName: `/${props.environment}/opendata/common/db_ckan`,
    });
    const pDbCkanUser = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbCkanUser', {
      parameterName: `/${props.environment}/opendata/common/db_ckan_user`,
    });
    const pDbDatastoreReadonly = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbDatastoreReadonly', {
      parameterName: `/${props.environment}/opendata/common/db_datastore_readonly`,
    });
    const pDbDatastoreReadonlyUser = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbDatastoreReadonlyUser', {
      parameterName: `/${props.environment}/opendata/common/db_datastore_readonly_user`,
    });
    const pDbDrupal = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbDrupal', {
      parameterName: `/${props.environment}/opendata/common/db_drupal`,
    });
    const pDbDrupalUser = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbDrupalUser', {
      parameterName: `/${props.environment}/opendata/common/db_drupal_user`,
    });
    const pSiteProtocol = ssm.StringParameter.fromStringParameterAttributes(this, 'pSiteProtocol', {
      parameterName: `/${props.environment}/opendata/common/site_protocol`,
    });
    const pRolesCkanAdmin = ssm.StringParameter.fromStringParameterAttributes(this, 'pRolesCkanAdmin', {
      parameterName: `/${props.environment}/opendata/common/roles_ckan_admin`,
    });
    const pSysadminUser = ssm.StringParameter.fromStringParameterAttributes(this, 'pSysadminUser', {
      parameterName: `/${props.environment}/opendata/common/sysadmin_user`,
    });
    const pSysadminEmail = ssm.StringParameter.fromStringParameterAttributes(this, 'pSysadminEmail', {
      parameterName: `/${props.environment}/opendata/common/sysadmin_email`,
    });
    const pSmtpHost = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpHost', {
      parameterName: `/${props.environment}/opendata/common/smtp_host`,
    });
    const pSmtpUsername = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpUsername', {
      parameterName: `/${props.environment}/opendata/common/smtp_username`,
    });
    const pSmtpFrom = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpFrom', {
      parameterName: `/${props.environment}/opendata/common/smtp_from`,
    });
    const pSmtpTo = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpTo', {
      parameterName: `/${props.environment}/opendata/common/smtp_to`,
    });
    const pSmtpFromError = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpFromError', {
      parameterName: `/${props.environment}/opendata/common/smtp_from_error`,
    });
    const pSmtpProtocol = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpProtocol', {
      parameterName: `/${props.environment}/opendata/common/smtp_protocol`,
    });
    const pSmtpPort = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpPort', {
      parameterName: `/${props.environment}/opendata/common/smtp_port`,
    });
    const pDisqusDomain = ssm.StringParameter.fromStringParameterAttributes(this, 'pDisqusDomain', {
      parameterName: `/${props.environment}/opendata/common/disqus_domain`,
    });

    // get secrets
    const sCkanSecrets = sm.Secret.fromSecretNameV2(this, 'sCkanSecrets', `/${props.environment}/opendata/ckan`);
    const sCommonSecrets = sm.Secret.fromSecretNameV2(this, 'sCommonSecrets', `/${props.environment}/opendata/common`);

    // ckan service
    this.ckanFsDataAccessPoint = props.fileSystems['ckan'].addAccessPoint('ckanFsDataAccessPoint', {
      path: '/ckan_data',
      createAcl: {
        ownerGid: '92',
        ownerUid: '92',
        permissions: '0755',
      },
      posixUser: {
        gid: '92',
        uid: '92',
      },
    });
    
    this.ckanFsResourcesAccessPoint = props.fileSystems['ckan'].addAccessPoint('ckanFsResourcesAccessPoint', {
      path: '/ckan_resources',
      createAcl: {
        ownerGid: '92',
        ownerUid: '92',
        permissions: '0755',
      },
      posixUser: {
        gid: '92',
        uid: '92',
      },
    });

    const ckanTaskDef = new ecs.FargateTaskDefinition(this, 'ckanTaskDef', {
      cpu: props.ckanTaskDef.taskCpu,
      memoryLimitMiB: props.ckanTaskDef.taskMem,
      volumes: [
        {
          name: 'ckan_data',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['ckan'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.ckanFsDataAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        },
        {
          name: 'ckan_resources',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['ckan'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.ckanFsResourcesAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        }
      ],
    });

    const ckanPluginsDefault: string[] = [
      'stats',
      'scheming_datasets',
      'scheming_groups',
      'scheming_organizations',
      'fluent',
    ];

    const ckanPlugins: string[] = [
      props.analyticsEnabled ? 'matomo' : '',
      props.cloudStorageEnabled ? 'cloudstorage' : '',
      'sentry',
      'ckan_harvester',
      'hri_harvester',
      'syke_harvester',
      'dcat',
      'structured_data',
      'dcat_rdf_harvester',
      'dcat_json_harvester',
      'dcat_json_interface',
      'ytp_spatial',
      'spatial_metadata',
      'spatial_query',
      'csw_harvester',
      'drupal8',
      'datarequests',
      'ytp_organizations',
      'ytp_request',
      'hierarchy_display',
      'disqus',
      'ytp_theme',
      'harvest',
      'report',
      'ytp_report',
      'ytp_drupal',
      'ytp_tasks',
      'ytp_dataset',
      'apis',
      'ytp_user',
      'datastore',
      'sixodp_showcase',
      'sixodp_showcasesubmit',
      'datapusher',
      'recline_grid_view',
      'recline_graph_view',
      'recline_map_view',
      'text_view',
      'image_view',
      'pdf_view',
      'resource_proxy',
      'geo_view',
      'geojson_view',
      'sixodp_harvester',
      'reminder',
      'ytp_restrict_category_creation_and_updating',
      'archiver',
      'qa',
      'ytp_ipermission_labels',
      'organizationapproval',
      'ytp_resourcestatus',
      'ytp_harvesterstatus',
      'opendata_group',
      'advancedsearch',
      'openapi_view',
      'statistics',
      'forcetranslation',
    ];

    const ckanContainerEnv: { [key: string]: string; } = {
      // .env.ckan
      CKAN_IMAGE_VERSION: pCkanImageVersion.stringValue,
      CKAN_SITE_URL: `https://${props.domainName}`,
      CKAN_SITE_ID: 'default',
      CKAN_PLUGINS_DEFAULT: ckanPluginsDefault.join(' '),
      CKAN_PLUGINS: ckanPlugins.join(' '),
      CKAN_STORAGE_PATH: '/srv/app/data',
      CKAN_ARCHIVER_PATH: '/srv/app/data/archiver',
      CKAN_WEBASSETS_PATH: '/srv/app/data/webassets',
      CKAN_ARCHIVER_SEND_NOTIFICATIONS: 'false',
      CKAN_ARCHIVER_EXEMPT_DOMAINS_FROM_BROKEN_LINK_NOTIFICATIONS: '',
      CKAN_HARVESTER_STATUS_RECIPIENTS: '',
      CKAN_HARVESTER_FAULT_RECIPIENTS: '',
      CKAN_HARVESTER_INSTRUCTION_URL: '',
      CKAN_MAX_RESOURCE_SIZE: '5000',
      CKAN_SHOW_POSTIT_DEMO: 'true',
      CKAN_PROFILING_ENABLED: 'false',
      CKAN_LOG_LEVEL: 'INFO',
      CKAN_EXT_LOG_LEVEL: 'INFO',
      CKAN_CLOUDSTORAGE_DRIVER: 'S3_EU_WEST',
      CKAN_CLOUDSTORAGE_CONTAINER_NAME: 'bucket-name',
      CKAN_CLOUDSTORAGE_USE_SECURE_URLS: '1',
      // .env
      CKAN_HOST: `ckan.${props.namespace.namespaceName}`,
      CKAN_PORT: '5000',
      DATAPUSHER_HOST: `datapusher.${props.namespace.namespaceName}`,
      DATAPUSHER_PORT: '8000',
      REDIS_HOST: props.cacheCluster.getAtt('RedisEndpoint.Address').toString(),
      REDIS_PORT: props.cachePort.toString(),
      REDIS_DB: '0',
      SOLR_HOST: `solr.${props.namespace.namespaceName}`,
      SOLR_PORT: '8983',
      SOLR_PATH: 'solr/ckan',
      NGINX_HOST: `nginx.${props.namespace.namespaceName}`,
      DB_HOST: pDbHost.stringValue,
      DB_CKAN: pDbCkan.stringValue,
      DB_CKAN_USER: pDbCkanUser.stringValue,
      DB_DATASTORE_READONLY: pDbDatastoreReadonly.stringValue,
      DB_DATASTORE_READONLY_USER: pDbDatastoreReadonlyUser.stringValue,
      DB_DRUPAL: pDbDrupal.stringValue,
      DB_DRUPAL_USER: pDbDrupalUser.stringValue,
      DOMAIN_NAME: props.domainName,
      SECONDARY_DOMAIN_NAME: props.secondaryDomainName,
      SITE_PROTOCOL: pSiteProtocol.stringValue,
      ROLES_CKAN_ADMIN: pRolesCkanAdmin.stringValue,
      SYSADMIN_USER: pSysadminUser.stringValue,
      SYSADMIN_EMAIL: pSysadminEmail.stringValue,
      SMTP_HOST: pSmtpHost.stringValue,
      SMTP_USERNAME: pSmtpUsername.stringValue,
      SMTP_FROM: pSmtpFrom.stringValue,
      SMTP_TO: pSmtpTo.stringValue,
      SMTP_FROM_ERROR: pSmtpFromError.stringValue,
      SMTP_PROTOCOL: pSmtpProtocol.stringValue,
      SMTP_PORT: pSmtpPort.stringValue,
      DISQUS_DOMAIN: pDisqusDomain.stringValue,
      SENTRY_ENV: props.environment,
      CKAN_SYSADMIN_NAME: pSysadminUser.stringValue,
      CKAN_SYSADMIN_EMAIL: pSysadminEmail.stringValue,
    };

    const ckanContainerSecrets: { [key: string]: ecs.Secret; } = {
      // .env.ckan
      CKAN_BEAKER_SESSION_SECRET: ecs.Secret.fromSecretsManager(sCkanSecrets, 'ckan_beaker_session_secret'),
      CKAN_APP_INSTANCE_UUID: ecs.Secret.fromSecretsManager(sCkanSecrets, 'ckan_app_instance_uuid'),
      // .env
      DB_CKAN_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'db_ckan_pass'),
      DB_DATASTORE_READONLY_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'db_datastore_readonly_pass'),
      DB_DRUPAL_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'db_drupal_pass'),
      SYSADMIN_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sysadmin_pass'),
      SMTP_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'smtp_pass'),
      CKAN_SYSADMIN_PASSWORD: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sysadmin_pass'),
      SENTRY_DSN: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sentry_dsn'),
    };

    if (props.analyticsEnabled) {
      // get params
      const pMatomoSiteId = ssm.StringParameter.fromStringParameterAttributes(this, 'pMatomoSiteId', {
        parameterName: `/${props.environment}/opendata/common/matomo_site_id`,
      });
      const pMatomoDomain = ssm.StringParameter.fromStringParameterAttributes(this, 'pMatomoDomain', {
        parameterName: `/${props.environment}/opendata/common/matomo_domain`,
      });
      const pMatomoScriptDomain = ssm.StringParameter.fromStringParameterAttributes(this, 'pMatomoScriptDomain', {
        parameterName: `/${props.environment}/opendata/common/matomo_script_domain`,
      });

      ckanContainerEnv['MATOMO_ENABLED'] = 'true';
      ckanContainerEnv['MATOMO_SITE_ID'] = pMatomoSiteId.stringValue;
      ckanContainerEnv['MATOMO_DOMAIN'] = pMatomoDomain.stringValue;
      ckanContainerEnv['MATOMO_SCRIPT_DOMAIN'] = pMatomoScriptDomain.stringValue;
      ckanContainerSecrets['MATOMO_TOKEN'] = ecs.Secret.fromSecretsManager(sCommonSecrets, 'matomo_token');
    } else {
      ckanContainerEnv['MATOMO_ENABLED'] = 'false';
      ckanContainerEnv['MATOMO_SITE_ID'] = '';
      ckanContainerEnv['MATOMO_DOMAIN'] = '';
      ckanContainerEnv['MATOMO_SCRIPT_DOMAIN'] = '';
      ckanContainerEnv['MATOMO_TOKEN'] = '';
    }

    if (props.captchaEnabled) {
      // get params
      const pRecaptchaPublicKey = ssm.StringParameter.fromStringParameterAttributes(this, 'pRecaptchaPublicKey', {
        parameterName: `/${props.environment}/opendata/common/recaptcha_public_key`,
      });

      ckanContainerEnv['CAPTCHA_ENABLED'] = 'true';
      ckanContainerEnv['RECAPTCHA_PUBLIC_KEY'] = pRecaptchaPublicKey.stringValue;
      ckanContainerSecrets['RECAPTCHA_PRIVATE_KEY'] = ecs.Secret.fromSecretsManager(sCommonSecrets, 'recaptcha_private_key');
    } else {
      ckanContainerEnv['CAPTCHA_ENABLED'] = 'false';
      ckanContainerEnv['RECAPTCHA_PUBLIC_KEY'] = '';
      ckanContainerEnv['RECAPTCHA_PRIVATE_KEY'] = '';
    }

    if (props.cloudStorageEnabled) {
      // get params
      const pCkanCloudstorageDriver = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanCloudstorageDriver', {
        parameterName: `/${props.environment}/opendata/ckan/cloudstorage_driver`,
      });
      const pCkanCloudstorageContainerName = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanCloudstorageContainerName', {
        parameterName: `/${props.environment}/opendata/ckan/cloudstorage_container_name`,
      });
      const pCkanCloudstorageUseSecureUrls = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanCloudstorageUseSecureUrls', {
        parameterName: `/${props.environment}/opendata/ckan/cloudstorage_use_secure_urls`,
      });

      ckanContainerEnv['CKAN_CLOUDSTORAGE_ENABLED'] = 'true';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_DRIVER'] = pCkanCloudstorageDriver.stringValue;
      ckanContainerEnv['CKAN_CLOUDSTORAGE_CONTAINER_NAME'] = pCkanCloudstorageContainerName.stringValue;
      ckanContainerEnv['CKAN_CLOUDSTORAGE_USE_SECURE_URLS'] = pCkanCloudstorageUseSecureUrls.stringValue;

      const ckanTaskExecPolicyAllowCloudstorage = new iam.PolicyStatement({
        actions: ['*'],
        resources: [
          `arn:aws:s3:::${pCkanCloudstorageContainerName.stringValue}`,
          `arn:aws:s3:::${pCkanCloudstorageContainerName.stringValue}/*`,
        ],
        effect: iam.Effect.ALLOW,
      });

      ckanTaskDef.addToExecutionRolePolicy(ckanTaskExecPolicyAllowCloudstorage);
    } else {
      ckanContainerEnv['CKAN_CLOUDSTORAGE_ENABLED'] = 'false';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_DRIVER'] = '';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_CONTAINER_NAME'] = '';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_USE_SECURE_URLS'] = '';
    }

    const ckanContainer = ckanTaskDef.addContainer('ckan', {
      image: ecs.ContainerImage.fromEcrRepository(props.repositories['ckan'], pCkanImageVersion.stringValue),
      environment: ckanContainerEnv,
      secrets: ckanContainerSecrets,
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'ckan-service',
      }),
    });

    ckanContainer.addPortMappings({
      containerPort: 5000,
      protocol: ecs.Protocol.TCP,
    });

    ckanContainer.addMountPoints({
      containerPath: '/srv/app/data',
      readOnly: false,
      sourceVolume: 'ckan_data',
    }, {
      containerPath: '/var/www/resources',
      readOnly: false,
      sourceVolume: 'ckan_resources',
    });

    this.ckanService = new ecs.FargateService(this, 'ckanService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: ckanTaskDef,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: cdk.Duration.minutes(1),
        name: 'ckan',
        container: ckanContainer,
        containerPort: 5000
      },
    });

    this.ckanService.connections.allowFrom(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan)');
    this.ckanService.connections.allowTo(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan)');
    this.ckanService.connections.allowTo(props.databaseSecurityGroup, ec2.Port.tcp(5432), 'RDS connection (ckan)');
    this.ckanService.connections.allowTo(props.cacheSecurityGroup, ec2.Port.tcp(props.cachePort), 'Redis connection (ckan)');
    
    const ckanServiceAsg = this.ckanService.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: 2,
    });

    ckanServiceAsg.scaleOnCpuUtilization('ckanServiceAsgPolicy', {
      targetUtilizationPercent: 50,
      scaleInCooldown: cdk.Duration.seconds(150),
      scaleOutCooldown: cdk.Duration.seconds(150),
    });

    // ckan cron service
    const ckanCronTaskDef = new ecs.FargateTaskDefinition(this, 'ckanCronTaskDef', {
      cpu: props.ckanCronTaskDef.taskCpu,
      memoryLimitMiB: props.ckanCronTaskDef.taskMem,
      volumes: [
        {
          name: 'ckan_data',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['ckan'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.ckanFsDataAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        }
      ],
    });

    const ckanCronContainer = ckanCronTaskDef.addContainer('ckan_cron', {
      image: ecs.ContainerImage.fromEcrRepository(props.repositories['ckan'], pCkanImageVersion.stringValue),
      environment: ckanContainerEnv,
      secrets: ckanContainerSecrets,
      entryPoint: ['/srv/app/entrypoint_cron.sh'],
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'ckan_cron-service',
      }),
    });

    ckanCronContainer.addMountPoints({
      containerPath: '/srv/app/data',
      readOnly: false,
      sourceVolume: 'ckan_data',
    });

    const ckanCronService = new ecs.FargateService(this, 'ckanCronService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: ckanCronTaskDef,
      desiredCount: 1,
      minHealthyPercent: 0,
      maxHealthyPercent: 100,
    });

    ckanCronService.connections.allowFrom(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan cron)');
    ckanCronService.connections.allowTo(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan cron)');
    ckanCronService.connections.allowTo(props.databaseSecurityGroup, ec2.Port.tcp(5432), 'RDS connection (ckan cron)');
    ckanCronService.connections.allowTo(props.cacheSecurityGroup, ec2.Port.tcp(props.cachePort), 'Redis connection (ckan cron)');

    const ckanCronServiceAsg = ckanCronService.autoScaleTaskCount({
      minCapacity: 0,
      maxCapacity: 1,
    });

    // datapusher service
    const datapusherTaskDef = new ecs.FargateTaskDefinition(this, 'datapusherTaskDef', {
      cpu: props.datapusherTaskDef.taskCpu,
      memoryLimitMiB: props.datapusherTaskDef.taskMem,
    });

    const datapusherContainer = datapusherTaskDef.addContainer('datapusher', {
      image: ecs.ContainerImage.fromEcrRepository(props.repositories['datapusher'], pDatapusherImageVersion.stringValue),
      environment: {
        // .env.datapusher
        DATAPUSHER_MAX_CONTENT_LENGTH: '10485760',
        DATAPUSHER_CHUNK_SIZE: '16384',
        DATAPUSHER_CHUNK_INSERT_ROWS: '250',
        DATAPUSHER_DOWNLOAD_TIMEOUT: '30',
        DATAPUSHER_SSL_VERIFY: 'False',
        DATAPUSHER_REWRITE_RESOURCES: 'True',
        // .env
        DATAPUSHER_REWRITE_URL: `http://ckan.${props.namespace.namespaceName}:5000/data`,
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'datapusher-service',
      }),
    });

    datapusherContainer.addPortMappings({
      containerPort: 8000,
      protocol: ecs.Protocol.TCP,
    });

    const datapusherService = new ecs.FargateService(this, 'datapusherService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: datapusherTaskDef,
      desiredCount: 1,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: cdk.Duration.minutes(1),
        name: 'datapusher',
        container: datapusherContainer,
        containerPort: 8000
      },
    });

    datapusherService.connections.allowFrom(this.ckanService, ec2.Port.tcp(8000), 'ckan - datapusher connection');
    datapusherService.connections.allowTo(this.ckanService, ec2.Port.tcp(5000), 'datapusher - ckan connection');

    const datapusherServiceAsg = datapusherService.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: 1,
    });

    // solr service
    this.solrFsDataAccessPoint = props.fileSystems['solr'].addAccessPoint('solrFsDataAccessPoint', {
      path: '/solr_data',
      createAcl: {
        ownerGid: '8983',
        ownerUid: '8983',
        permissions: '0755',
      },
      posixUser: {
        gid: '8983',
        uid: '8983',
      },
    });

    const solrTaskDef = new ecs.FargateTaskDefinition(this, 'solrTaskDef', {
      cpu: props.solrTaskDef.taskCpu,
      memoryLimitMiB: props.solrTaskDef.taskMem,
      volumes: [
        {
          name: 'solr_data',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['solr'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.solrFsDataAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        }
      ],
    });

    const solrContainer = solrTaskDef.addContainer('solr', {
      image: ecs.ContainerImage.fromEcrRepository(props.repositories['solr'], pSolrImageVersion.stringValue),
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'solr-service',
      }),
    });

    solrContainer.addPortMappings({
      containerPort: 8983,
      protocol: ecs.Protocol.TCP,
    });

    solrContainer.addMountPoints({
      containerPath: '/opt/solr/server/solr/ckan/data',
      readOnly: false,
      sourceVolume: 'solr_data',
    });

    const solrService = new ecs.FargateService(this, 'solrService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: solrTaskDef,
      desiredCount: 1,
      minHealthyPercent: 0,
      maxHealthyPercent: 100,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: cdk.Duration.minutes(1),
        name: 'solr',
        container: solrContainer,
        containerPort: 8983
      },
    });

    solrService.connections.allowFrom(props.fileSystems['solr'], ec2.Port.tcp(2049), 'EFS connection (solr)');
    solrService.connections.allowTo(props.fileSystems['solr'], ec2.Port.tcp(2049), 'EFS connection (solr)');
    solrService.connections.allowFrom(this.ckanService, ec2.Port.tcp(8983), 'ckan - solr connection');
    solrService.connections.allowFrom(ckanCronService, ec2.Port.tcp(8983), 'ckan_cron - solr connection');

    const solrServiceAsg = solrService.autoScaleTaskCount({
      minCapacity: 0,
      maxCapacity: 1,
    });
  }
}
