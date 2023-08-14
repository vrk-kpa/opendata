import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as sd from 'aws-cdk-lib/aws-servicediscovery';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import * as efs from 'aws-cdk-lib/aws-efs';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

import { CkanStackProps } from './ckan-stack-props';
import { parseEcrAccountId, parseEcrRegion } from './common-stack-funcs';
import {ISecret} from "aws-cdk-lib/aws-secretsmanager";
import {Key} from "aws-cdk-lib/aws-kms";
import {Effect, PolicyStatement} from "aws-cdk-lib/aws-iam";

export class CkanStack extends Stack {
  readonly ckanFsDataAccessPoint: efs.IAccessPoint;
  readonly solrFsDataAccessPoint: efs.IAccessPoint;
  readonly fusekiFsDataAccessPoint: efs.IAccessPoint;
  readonly migrationFsAccessPoint?: efs.IAccessPoint;
  readonly ckanService: ecs.FargateService;
  readonly ckanCronService?: ecs.FargateService;

  constructor(scope: Construct, id: string, props: CkanStackProps) {
    super(scope, id, props);

    // get params
    const pCkanHarvesterStatusRecipients = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanHarvesterStatusRecipients', {
      parameterName: `/${props.environment}/opendata/ckan/harvester_status_recipients`,
    });
    const pCkanHarvesterFaultRecipients = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanHarvesterFaultRecipients', {
      parameterName: `/${props.environment}/opendata/ckan/harvester_fault_recipients`,
    });
    const pCkanHarvesterInstructionUrl = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanHarvesterInstructionUrl', {
      parameterName: `/${props.environment}/opendata/ckan/harvester_instruction_url`,
    });

    const host = props.databaseInstance.instanceEndpoint;

    const datastoreHost = props.datastoreInstance.instanceEndpoint;

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
    const pFusekiAdminUser = ssm.StringParameter.fromStringParameterAttributes(this, 'pFusekiAdminUser', {
      parameterName: `/${props.environment}/opendata/common/fuseki_admin_user`,
    });

    const encryptionKey = Key.fromLookup(this, 'EncryptionKey', {
      aliasName: `alias/secrets-key-${props.environment}`
    })



    // get secrets
    const sCkanSecrets = sm.Secret.fromSecretNameV2(this, 'sCkanSecrets', `/${props.environment}/opendata/ckan`);
    const sCommonSecrets = sm.Secret.fromSecretNameV2(this, 'sCommonSecrets', `/${props.environment}/opendata/common`);

    // get repositories
    const ckanRepo = ecr.Repository.fromRepositoryArn(this, 'ckanRepo', `arn:aws:ecr:${parseEcrRegion(props.envProps.REGISTRY)}:${parseEcrAccountId(props.envProps.REGISTRY)}:repository/${props.envProps.REPOSITORY}/ckan`);
    const datapusherRepo = ecr.Repository.fromRepositoryArn(this, 'datapusherRepo', `arn:aws:ecr:${parseEcrRegion(props.envProps.REGISTRY)}:${parseEcrAccountId(props.envProps.REGISTRY)}:repository/${props.envProps.REPOSITORY}/datapusher`);
    const solrRepo = ecr.Repository.fromRepositoryArn(this, 'solrRepo', `arn:aws:ecr:${parseEcrRegion(props.envProps.REGISTRY)}:${parseEcrAccountId(props.envProps.REGISTRY)}:repository/${props.envProps.REPOSITORY}/solr`);

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
      'forcetranslation',
      'sentry',
      'ckan_harvester',
      'hri_harvester',
      'syke_harvester',
      'dcat',
      'structured_data',
      'dcat_rdf_harvester',
      'dcat_json_harvester',
      'dcat_json_interface',
      'csw_harvester',
      'drupal8',
      //'datarequests',
      'ytp_organizations',
      'ytp_request',
      'hierarchy_display',
      'ytp_theme',
      'harvest',
      'report',
      'ytp_report',
      'ytp_drupal',
      'ytp_tasks',
      'ytp_dataset',
      'apis',
      'ytp_spatial',
      'spatial_metadata',
      'spatial_query',
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
      'opendata_cli',
      'ytp_recommendation',
      'dcat_sparql',
      'sitesearch',
    ];

    const ckanContainerEnv: { [key: string]: string; } = {
      // .env.ckan
      CKAN_IMAGE_TAG: props.envProps.CKAN_IMAGE_TAG,
      CKAN_SITE_URL: `https://${props.domainName}`,
      CKAN_DRUPAL_SITE_URL: `https://${props.domainName}`,
      CKAN_SITE_ID: 'default',
      CKAN_PLUGINS_DEFAULT: ckanPluginsDefault.join(' '),
      CKAN_PLUGINS: ckanPlugins.join(' '),
      CKAN_STORAGE_PATH: '/srv/app/data',
      CKAN_ARCHIVER_PATH: '/srv/app/data/archiver',
      CKAN_WEBASSETS_PATH: '/srv/app/data/webassets',
      CKAN_ARCHIVER_SEND_NOTIFICATION_EMAILS_TO_MAINTAINERS: String(props.archiverSendNotificationEmailsToMaintainers),
      CKAN_ARCHIVER_EXEMPT_DOMAINS_FROM_BROKEN_LINK_NOTIFICATIONS: props.archiverExemptDomainsFromBrokenLinkNotifications.join(' '),
      CKAN_HARVESTER_STATUS_RECIPIENTS: pCkanHarvesterStatusRecipients.stringValue,
      CKAN_HARVESTER_FAULT_RECIPIENTS: pCkanHarvesterFaultRecipients.stringValue,
      CKAN_HARVESTER_INSTRUCTION_URL: pCkanHarvesterInstructionUrl.stringValue,
      CKAN_MAX_RESOURCE_SIZE: '5000',
      CKAN_SHOW_POSTIT_DEMO: 'true',
      CKAN_PROFILING_ENABLED: 'false',
      CKAN_LOG_LEVEL: 'INFO',
      CKAN_EXT_LOG_LEVEL: 'INFO',
      // .env
      CKAN_HOST: `ckan.${props.namespace.namespaceName}`,
      CKAN_PORT: '5000',
      DATAPUSHER_HOST: `datapusher.${props.namespace.namespaceName}`,
      DATAPUSHER_PORT: '8800',
      REDIS_HOST: props.cacheCluster.getAtt('RedisEndpoint.Address').toString(),
      REDIS_PORT: props.cachePort.toString(),
      REDIS_DB: '0',
      SOLR_HOST: `solr.${props.namespace.namespaceName}`,
      SOLR_PORT: '8983',
      SOLR_PATH: 'solr/ckan',
      NGINX_HOST: `nginx.${props.namespace.namespaceName}`,
      DB_CKAN_HOST: host.hostname,
      DB_CKAN: "ckan_default",
      DB_CKAN_USER: "ckan_default",
      DB_DATASTORE_HOST: datastoreHost.hostname,
      DB_DATASTORE: "datastore",
      DB_DATASTORE_ADMIN: props.datastoreCredentials.username,
      DB_DATASTORE_USER: props.datastoreUserCredentials.username,
      DB_DATASTORE_READONLY_USER: props.datastoreReadCredentials.username,
      DB_DRUPAL_HOST: host.hostname,
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
      SENTRY_ENV: props.environment,
      CKAN_SYSADMIN_NAME: pSysadminUser.stringValue,
      CKAN_SYSADMIN_EMAIL: pSysadminEmail.stringValue,
      // fuseki
      FUSEKI_HOST: `fuseki.${props.namespace.namespaceName}`,
      FUSEKI_PORT: '3030',
      FUSEKI_ADMIN_USER: pFusekiAdminUser.stringValue,
      FUSEKI_OPENDATA_DATASET: 'opendata',
    };

    const ckanContainerSecrets: { [key: string]: ecs.Secret; } = {
      // .env.ckan
      CKAN_BEAKER_SESSION_SECRET: ecs.Secret.fromSecretsManager(sCkanSecrets, 'ckan_beaker_session_secret'),
      CKAN_APP_INSTANCE_UUID: ecs.Secret.fromSecretsManager(sCkanSecrets, 'ckan_app_instance_uuid'),
      // .env
      DB_CKAN_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'db_ckan_pass'),
      DB_DATASTORE_PASS: ecs.Secret.fromSecretsManager(<ISecret>props.datastoreUserCredentials.secret, 'password'),
      DB_DATASTORE_READONLY_PASS: ecs.Secret.fromSecretsManager(<ISecret>props.datastoreReadCredentials.secret, 'password'),
      DB_DRUPAL_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'db_drupal_pass'),
      SYSADMIN_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sysadmin_pass'),
      SMTP_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'smtp_pass'),
      CKAN_SYSADMIN_PASSWORD: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sysadmin_pass'),
      SENTRY_DSN: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sentry_dsn'),
      FUSEKI_ADMIN_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'fuseki_admin_pass'),
    };

    ckanTaskDef.addToExecutionRolePolicy(new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        "kms:Decrypt"
      ],
      resources: [
        encryptionKey.keyArn
      ]
    }));


    if (ckanTaskDef.executionRole !== undefined) {
      if (props.datastoreUserCredentials.secret !== undefined && props.datastoreReadCredentials.secret !== undefined) {
        props.datastoreUserCredentials.secret.grantRead(ckanTaskDef.executionRole);
        props.datastoreReadCredentials.secret.grantRead(ckanTaskDef.executionRole);
      }
    }


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

    if (props.cloudstorageEnabled) {
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
      ckanContainerEnv['CKAN_CLOUDSTORAGE_AWS_USE_BOTO3_SESSIONS'] = '1';

      const ckanTaskExecPolicyAllowCloudstorage = new iam.PolicyStatement({
        actions: ['*'],
        resources: [
          `arn:aws:s3:::${pCkanCloudstorageContainerName.stringValue}`,
          `arn:aws:s3:::${pCkanCloudstorageContainerName.stringValue}/*`,
        ],
        effect: iam.Effect.ALLOW,
      });

      ckanTaskDef.addToTaskRolePolicy(ckanTaskExecPolicyAllowCloudstorage);
    } else {
      ckanContainerEnv['CKAN_CLOUDSTORAGE_ENABLED'] = 'false';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_DRIVER'] = '';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_CONTAINER_NAME'] = '';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_USE_SECURE_URLS'] = '';
      ckanContainerEnv['CKAN_CLOUDSTORAGE_AWS_USE_BOTO3_SESSIONS'] = '0';
    }

    const ckanLogGroup = new logs.LogGroup(this, 'ckanLogGroup', {
      logGroupName: `/${props.environment}/opendata/ckan`,
    });

    const ckanContainer = ckanTaskDef.addContainer('ckan', {
      image: ecs.ContainerImage.fromEcrRepository(ckanRepo, props.envProps.CKAN_IMAGE_TAG),
      environment: ckanContainerEnv,
      secrets: ckanContainerSecrets,
      logging: ecs.LogDrivers.awsLogs({
        logGroup: ckanLogGroup,
        streamPrefix: 'ckan-service',
      }),
      healthCheck: {
        command: ['CMD-SHELL', 'curl --fail http://localhost:5000/api/3/action/status_show --user-agent "docker-healthcheck" || exit 1'],
        interval: Duration.seconds(15),
        timeout: Duration.seconds(5),
        retries: 5,
        startPeriod: Duration.seconds(300),
      },
      linuxParameters: new ecs.LinuxParameters(this, 'ckanContainerLinuxParams', {
        initProcessEnabled: true,
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
    });

    const ckanTaskPolicyAllowExec = new iam.PolicyStatement({
      actions: [
        'ssmmessages:CreateControlChannel',
        'ssmmessages:CreateDataChannel',
        'ssmmessages:OpenControlChannel',
        'ssmmessages:OpenDataChannel',
      ],
      resources: ['*'],
      effect: iam.Effect.ALLOW,
    });

    ckanTaskDef.addToTaskRolePolicy(ckanTaskPolicyAllowExec);

    this.ckanService = new ecs.FargateService(this, 'ckanService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: ckanTaskDef,
      minHealthyPercent: 50,
      maxHealthyPercent: 200,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: Duration.minutes(1),
        name: 'ckan',
        container: ckanContainer,
        containerPort: 5000
      },
      enableExecuteCommand: true,
    });

    this.ckanService.connections.allowFrom(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan)');
    this.ckanService.connections.allowTo(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan)');
    this.ckanService.connections.allowTo(props.databaseSecurityGroup, ec2.Port.tcp(5432), 'RDS connection (ckan)');
    this.ckanService.connections.allowTo(props.datastoreSecurityGroup, ec2.Port.tcp(5432), 'RDS datastore connection (ckan)')
    this.ckanService.connections.allowTo(props.cacheSecurityGroup, ec2.Port.tcp(props.cachePort), 'Redis connection (ckan)');

    const ckanServiceAsg = this.ckanService.autoScaleTaskCount({
      minCapacity: props.ckanTaskDef.taskMinCapacity,
      maxCapacity: props.ckanTaskDef.taskMaxCapacity,
    });

    ckanServiceAsg.scaleOnCpuUtilization('ckanServiceAsgPolicy', {
      targetUtilizationPercent: 50,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60),
    });

    ckanServiceAsg.scaleOnMemoryUtilization('ckanServiceAsgPolicyMem', {
      targetUtilizationPercent: 80,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60),
    });

    // mount migration filesystem if given
    if (props.migrationFileSystemProps != null) {
      this.migrationFsAccessPoint = new efs.AccessPoint(this, 'migrationFsAccessPoint', {
        fileSystem: props.migrationFileSystemProps.fileSystem,
        path: '/ytp_files',
        posixUser: {
          gid: '0',
          uid: '0',
        },
      });

      props.migrationFileSystemProps.fileSystem.grant(ckanTaskDef.taskRole, 'elasticfilesystem:ClientRootAccess');

      ckanTaskDef.addVolume({
        name: 'ytp_files',
        efsVolumeConfiguration: {
          fileSystemId: props.migrationFileSystemProps.fileSystem.fileSystemId,
          authorizationConfig: {
            accessPointId: this.migrationFsAccessPoint.accessPointId,
          },
          transitEncryption: 'ENABLED',
        },
      });

      // NOTE: ckan storage path will be in: /mnt/ytp_files/ckan
      ckanContainer.addMountPoints({
        containerPath: '/mnt/ytp_files',
        readOnly: true,
        sourceVolume: 'ytp_files',
      });

      this.ckanService.connections.allowFrom(props.migrationFileSystemProps.securityGroup, ec2.Port.tcp(2049), 'EFS connection (ckan migrate)');
      this.ckanService.connections.allowTo(props.migrationFileSystemProps.securityGroup, ec2.Port.tcp(2049), 'EFS connection (ckan migrate)');
    }

    // ckan cron service
    if (props.ckanCronEnabled) {
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

      const ckanCronLogGroup = new logs.LogGroup(this, 'ckanCronLogGroup', {
        logGroupName: `/${props.environment}/opendata/ckan_cron`,
      });

      const ckanCronContainer = ckanCronTaskDef.addContainer('ckan_cron', {
        image: ecs.ContainerImage.fromEcrRepository(ckanRepo, props.envProps.CKAN_IMAGE_TAG),
        environment: ckanContainerEnv,
        secrets: ckanContainerSecrets,
        entryPoint: ['/srv/app/scripts/entrypoint_cron.sh'],
        user: "root",
        logging: ecs.LogDrivers.awsLogs({
          logGroup: ckanCronLogGroup,
          streamPrefix: 'ckan_cron-service',
        }),
        healthCheck: {
          command: ['CMD-SHELL', 'ps aux | grep -o "[c]rond -f" && ps aux | grep -o "[s]upervisord --configuration"'],
          interval: Duration.seconds(15),
          timeout: Duration.seconds(5),
          retries: 5,
          startPeriod: Duration.seconds(60),
        },
      });

      ckanCronContainer.addMountPoints({
        containerPath: '/srv/app/data',
        readOnly: false,
        sourceVolume: 'ckan_data',
      });

      ckanCronTaskDef.addToTaskRolePolicy(ckanTaskPolicyAllowExec);

      ckanCronTaskDef.addToExecutionRolePolicy(new PolicyStatement({
        effect: Effect.ALLOW,
        actions: [
          "kms:Decrypt"
        ],
        resources: [
          encryptionKey.keyArn
        ]
      }));

      if (ckanCronTaskDef.executionRole !== undefined) {
        if (props.datastoreCredentials.secret !== undefined && props.datastoreReadCredentials.secret !== undefined) {
          props.datastoreCredentials.secret.grantRead(ckanCronTaskDef.executionRole);
          props.datastoreReadCredentials.secret.grantRead(ckanCronTaskDef.executionRole);
        }
      }

      this.ckanCronService = new ecs.FargateService(this, 'ckanCronService', {
        platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
        cluster: props.cluster,
        taskDefinition: ckanCronTaskDef,
        desiredCount: 1,
        minHealthyPercent: 0,
        maxHealthyPercent: 100,
        enableExecuteCommand: true
      });

      this.ckanCronService.connections.allowFrom(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan cron)');
      this.ckanCronService.connections.allowTo(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (ckan cron)');
      this.ckanCronService.connections.allowTo(props.databaseSecurityGroup, ec2.Port.tcp(5432), 'RDS connection (ckan cron)');
      this.ckanService.connections.allowTo(props.datastoreSecurityGroup, ec2.Port.tcp(5432), 'RDS datastore connection (ckan cron)')
      this.ckanCronService.connections.allowTo(props.cacheSecurityGroup, ec2.Port.tcp(props.cachePort), 'Redis connection (ckan cron)');

      const ckanCronServiceAsg = this.ckanCronService.autoScaleTaskCount({
        minCapacity: props.ckanCronTaskDef.taskMinCapacity,
        maxCapacity: props.ckanCronTaskDef.taskMaxCapacity,
      });
    }

    // datapusher service
    const datapusherTaskDef = new ecs.FargateTaskDefinition(this, 'datapusherTaskDef', {
      cpu: props.datapusherTaskDef.taskCpu,
      memoryLimitMiB: props.datapusherTaskDef.taskMem,
    });


    const datapusherContainerEnv: { [key: string]: string; } = {
      ADD_SUMMARY_STATS_RESOURCE: 'False',
      PORT: '8800',
      MAX_CONTENT_LENGTH: '5242880000',
      DB_DATASTORE_HOST: datastoreHost.hostname,
      DB_DATASTORE: "datastore",
      DB_DATASTORE_USER: props.datastoreCredentials.username,
      DB_DATAPUSHER_JOBS_HOST: datastoreHost.hostname,
      DB_DATAPUSHER_JOBS: "datapusher_jobs",
      DB_DATAPUSHER_JOBS_USER: props.datastoreJobsCredentials.username,
    }

    const datapusherLogGroup = new logs.LogGroup(this, 'datapusherLogGroup', {
      logGroupName: `/${props.environment}/opendata/datapusher`,
    });

    const datapusherContainerSecrets: { [key: string]: ecs.Secret; } = {
      DB_DATASTORE_PASS: ecs.Secret.fromSecretsManager(<ISecret>props.datastoreUserCredentials.secret, 'password'),
      DB_DATAPUSHER_JOBS_PASS: ecs.Secret.fromSecretsManager(<ISecret>props.datastoreJobsCredentials.secret, 'password')
    };

    datapusherTaskDef.addToExecutionRolePolicy(new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        "kms:Decrypt"
      ],
      resources: [
        encryptionKey.keyArn
      ]
    }));

    if (props.datastoreJobsCredentials.secret !== undefined && props.datastoreUserCredentials.secret !== undefined
      && datapusherTaskDef.executionRole !== undefined) {
      props.datastoreJobsCredentials.secret.grantRead(datapusherTaskDef.executionRole)
      props.datastoreUserCredentials.secret.grantRead(datapusherTaskDef.executionRole)
    }

    const datapusherContainer = datapusherTaskDef.addContainer('datapusher', {
      image: ecs.ContainerImage.fromEcrRepository(datapusherRepo, props.envProps.DATAPUSHER_IMAGE_TAG),
      environment: datapusherContainerEnv,
      secrets: datapusherContainerSecrets,
      logging: ecs.LogDrivers.awsLogs({
        logGroup: datapusherLogGroup,
        streamPrefix: 'datapusher-service',
      }),
      //healthCheck: {
      //  command: ['CMD-SHELL', 'curl --fail http://localhost:8800/status || exit 1'],
      //  interval: Duration.seconds(15),
      //  timeout: Duration.seconds(5),
      //  retries: 5,
      //  startPeriod: Duration.seconds(15),
      //},
    });


    datapusherContainer.addPortMappings({
      containerPort: 8800,
      protocol: ecs.Protocol.TCP,
    });


    datapusherTaskDef.addToTaskRolePolicy(ckanTaskPolicyAllowExec);

    const datapusherService = new ecs.FargateService(this, 'datapusherService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: datapusherTaskDef,
      desiredCount: 1,
      minHealthyPercent: 50,
      maxHealthyPercent: 200,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: Duration.minutes(1),
        name: 'datapusher',
        container: datapusherContainer,
        containerPort: 8800
      },
      enableExecuteCommand: true
    });

    datapusherService.connections.allowFrom(this.ckanService, ec2.Port.tcp(8800), 'ckan - datapusher connection');
    datapusherService.connections.allowTo(this.ckanService, ec2.Port.tcp(5000), 'datapusher - ckan connection');
    datapusherService.connections.allowTo(props.datastoreSecurityGroup, ec2.Port.tcp(5432), 'RDS connection (datapusher)');

    const datapusherServiceAsg = datapusherService.autoScaleTaskCount({
      minCapacity: props.datapusherTaskDef.taskMinCapacity,
      maxCapacity: props.datapusherTaskDef.taskMaxCapacity,
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

    const solrLogGroup = new logs.LogGroup(this, 'solrLogGroup', {
      logGroupName: `/${props.environment}/opendata/solr`,
    });

    const solrContainer = solrTaskDef.addContainer('solr', {
      image: ecs.ContainerImage.fromEcrRepository(solrRepo, props.envProps.SOLR_IMAGE_TAG),
      logging: ecs.LogDrivers.awsLogs({
        logGroup: solrLogGroup,
        streamPrefix: 'solr-service',
      }),
      healthCheck: {
        command: ['CMD-SHELL', 'curl --fail -s http://localhost:8983/solr/ckan/admin/ping?wt=json | grep -o "OK"'],
        interval: Duration.seconds(15),
        timeout: Duration.seconds(5),
        retries: 5,
        startPeriod: Duration.seconds(15),
      },
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
        dnsTtl: Duration.minutes(1),
        name: 'solr',
        container: solrContainer,
        containerPort: 8983
      },
    });

    solrService.connections.allowFrom(props.fileSystems['solr'], ec2.Port.tcp(2049), 'EFS connection (solr)');
    solrService.connections.allowTo(props.fileSystems['solr'], ec2.Port.tcp(2049), 'EFS connection (solr)');
    solrService.connections.allowFrom(this.ckanService, ec2.Port.tcp(8983), 'ckan - solr connection');
    if (props.ckanCronEnabled) {
      this.ckanCronService?.connections.allowTo(solrService, ec2.Port.tcp(8983), 'ckan_cron - solr connection');
    }

    const solrServiceAsg = solrService.autoScaleTaskCount({
      minCapacity: props.solrTaskDef.taskMinCapacity,
      maxCapacity: props.solrTaskDef.taskMaxCapacity,
    });
    // fuseki service
    this.fusekiFsDataAccessPoint = props.fileSystems['fuseki'].addAccessPoint('fusekiFsDataAccessPoint', {
      path: '/fuseki_data',
      createAcl: {
        ownerGid: '3030',
        ownerUid: '3030',
        permissions: '0755',
      },
      posixUser: {
        gid: '3030',
        uid: '3030',
      },
    });

    const fusekiTaskDef = new ecs.FargateTaskDefinition(this, 'fusekiTaskDef', {
      cpu: props.fusekiTaskDef.taskCpu,
      memoryLimitMiB: props.fusekiTaskDef.taskMem,
      volumes: [
        {
          name: 'fuseki_data',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['fuseki'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.fusekiFsDataAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        }
      ],
    });

    const fusekiLogGroup = new logs.LogGroup(this, 'fusekiLogGroup', {
      logGroupName: `/${props.environment}/opendata/fuseki`,
    });

    const fusekiContainerSecrets: { [key: string]: ecs.Secret; } = {
      ADMIN_PASSWORD: ecs.Secret.fromSecretsManager(sCommonSecrets, 'fuseki_admin_pass'),
    };

    const fusekiContainer = fusekiTaskDef.addContainer('fuseki', {
      image: ecs.ContainerImage.fromRegistry(`stain/jena-fuseki:${props.envProps.FUSEKI_IMAGE_TAG}`),
      secrets: fusekiContainerSecrets,
      logging: ecs.LogDrivers.awsLogs({
        logGroup: fusekiLogGroup,
        streamPrefix: 'fuseki-service',
      }),
      healthCheck: {
        command: ['CMD-SHELL', 'curl --fail -s http://localhost:3030/$/ping'],
        interval: Duration.seconds(15),
        timeout: Duration.seconds(5),
        retries: 5,
        startPeriod: Duration.seconds(15),
      },
      environment: {
        FUSEKI_DATASET_1: ckanContainerEnv.FUSEKI_OPENDATA_DATASET,
      }
    });

    fusekiContainer.addPortMappings({
      containerPort: 3030,
      protocol: ecs.Protocol.TCP,
    });

    fusekiContainer.addMountPoints({
      containerPath: '/fuseki',
      readOnly: false,
      sourceVolume: 'fuseki_data',
    });

    const fusekiService = new ecs.FargateService(this, 'fusekiService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: fusekiTaskDef,
      desiredCount: 1,
      minHealthyPercent: 0,
      maxHealthyPercent: 100,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: Duration.minutes(1),
        name: 'fuseki',
        container: fusekiContainer,
        containerPort: 3030
      },
    });

    fusekiService.connections.allowFrom(props.fileSystems['fuseki'], ec2.Port.tcp(2049), 'EFS connection (fuseki)');
    fusekiService.connections.allowTo(props.fileSystems['fuseki'], ec2.Port.tcp(2049), 'EFS connection (fuseki)');
    fusekiService.connections.allowFrom(this.ckanService, ec2.Port.tcp(3030), 'ckan - fuseki connection');
    if (props.ckanCronEnabled) {
      this.ckanCronService?.connections.allowTo(fusekiService, ec2.Port.tcp(3030), 'ckan_cron - fuseki connection');
    }

    const fusekiServiceAsg = fusekiService.autoScaleTaskCount({
      minCapacity: props.fusekiTaskDef.taskMinCapacity,
      maxCapacity: props.fusekiTaskDef.taskMaxCapacity,
    });
  }
}
