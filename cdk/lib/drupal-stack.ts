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

import { DrupalStackProps } from './drupal-stack-props';
import { DrupalUser } from './drupal-user';
import { parseEcrAccountId, parseEcrRegion } from './common-stack-funcs';

export class DrupalStack extends Stack {
  readonly drupalFsDataAccessPoint: efs.IAccessPoint;
  readonly migrationFsAccessPoint?: efs.IAccessPoint;
  readonly drupalService: ecs.FargateService;

  constructor(scope: Construct, id: string, props: DrupalStackProps) {
    super(scope, id, props);

    // get params

    const host = props.databaseInstance.instanceEndpoint

    const pDbDrupal = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbDrupal', {
      parameterName: `/${props.environment}/opendata/common/db_drupal`,
    });
    const pDbDrupalUser = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbDrupalUser', {
      parameterName: `/${props.environment}/opendata/common/db_drupal_user`,
    });
    const pSiteName = ssm.StringParameter.fromStringParameterAttributes(this, 'pSiteName', {
      parameterName: `/${props.environment}/opendata/common/site_name`,
    });
    const pRolesCkanAdmin = ssm.StringParameter.fromStringParameterAttributes(this, 'pRolesCkanAdmin', {
      parameterName: `/${props.environment}/opendata/common/roles_ckan_admin`,
    });
    const pRolesEditor = ssm.StringParameter.fromStringParameterAttributes(this, 'pRolesEditor', {
      parameterName: `/${props.environment}/opendata/common/roles_editor`,
    });
    const pRolesPublisher = ssm.StringParameter.fromStringParameterAttributes(this, 'pRolesPublisher', {
      parameterName: `/${props.environment}/opendata/common/roles_publisher`,
    });
    const pSysadminUser = ssm.StringParameter.fromStringParameterAttributes(this, 'pSysadminUser', {
      parameterName: `/${props.environment}/opendata/common/sysadmin_user`,
    });
    const pSysadminEmail = ssm.StringParameter.fromStringParameterAttributes(this, 'pSysadminEmail', {
      parameterName: `/${props.environment}/opendata/common/sysadmin_email`,
    });
    const pSysadminRoles = ssm.StringParameter.fromStringParameterAttributes(this, 'pSysadminRoles', {
      parameterName: `/${props.environment}/opendata/common/sysadmin_roles`,
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
    const pSmtpProtocol = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpProtocol', {
      parameterName: `/${props.environment}/opendata/common/smtp_protocol`,
    });
    const pSmtpPort = ssm.StringParameter.fromStringParameterAttributes(this, 'pSmtpPort', {
      parameterName: `/${props.environment}/opendata/common/smtp_port`,
    });

    let pUsers: DrupalUser[];
    switch (props.environment) {
      case 'prod': {
        pUsers = [
        ];
      } break;
      default: {
        pUsers = [
        ];
      } break;
    }

    // get secrets
    const sDrupalSecrets = sm.Secret.fromSecretNameV2(this, 'sDrupalSecrets', `/${props.environment}/opendata/drupal`);
    const sCommonSecrets = sm.Secret.fromSecretNameV2(this, 'sCommonSecrets', `/${props.environment}/opendata/common`);

    // get repositories
    const drupalRepo = ecr.Repository.fromRepositoryArn(this, 'drupalRepo', `arn:aws:ecr:${parseEcrRegion(props.envProps.REGISTRY)}:${parseEcrAccountId(props.envProps.REGISTRY)}:repository/${props.envProps.REPOSITORY}/drupal`);

    this.drupalFsDataAccessPoint = props.fileSystems['drupal'].addAccessPoint('drupalFsSitesAccessPoint', {
      path: '/drupal_sites',
      createAcl: {
        ownerGid: '0',
        ownerUid: '0',
        permissions: '0755',
      },
      posixUser: {
        gid: '0',
        uid: '0',
      },
    });

    const drupalTaskDef = new ecs.FargateTaskDefinition(this, 'drupalTaskDef', {
      cpu: props.drupalTaskDef.taskCpu,
      memoryLimitMiB: props.drupalTaskDef.taskMem,
      volumes: [
        {
          name: 'drupal_sites',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['drupal'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.drupalFsDataAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        }
      ],
    });

    props.fileSystems['drupal'].grant(drupalTaskDef.taskRole, 'elasticfilesystem:ClientRootAccess');

    let drupalContainerEnv: { [key: string]: string; } = {
      // .env.drupal
      DRUPAL_IMAGE_TAG: props.envProps.DRUPAL_IMAGE_TAG,
      DRUPAL_CONFIG_SYNC_DIRECTORY: '/opt/drupal/web/sites/default/sync',
      // .env
      DB_DRUPAL_HOST: host.hostname,
      DB_DRUPAL: pDbDrupal.stringValue,
      DB_DRUPAL_USER: pDbDrupalUser.stringValue,
      DOMAIN_NAME: props.domainName,
      SECONDARY_DOMAIN_NAME: props.secondaryDomainName,
      SITE_NAME: pSiteName.stringValue,
      ROLES_CKAN_ADMIN: pRolesCkanAdmin.stringValue,
      ROLES_EDITOR: pRolesEditor.stringValue,
      ROLES_PUBLISHER: pRolesPublisher.stringValue,
      SYSADMIN_USER: pSysadminUser.stringValue,
      SYSADMIN_EMAIL: pSysadminEmail.stringValue,
      SYSADMIN_ROLES: pSysadminRoles.stringValue,
      NGINX_HOST: `nginx.${props.namespace.namespaceName}`,
      SMTP_HOST: pSmtpHost.stringValue,
      SMTP_USERNAME: pSmtpUsername.stringValue,
      SMTP_FROM: pSmtpFrom.stringValue,
      SMTP_PROTOCOL: pSmtpProtocol.stringValue,
      SMTP_PORT: pSmtpPort.stringValue,
      SENTRY_ENV: props.environment,
      SENTRY_TRACES_SAMPLE_RATE: props.sentryTracesSampleRate,
      BYPASS_CDN_DOMAIN: `vip.${props.fqdn}`
    };

    let drupalContainerSecrets: { [key: string]: ecs.Secret; } = {
      // .env.drupal
      DRUPAL_HASH_SALT: ecs.Secret.fromSecretsManager(sDrupalSecrets, 'drupal_hash_salt'),
      // .env
      DB_DRUPAL_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'db_drupal_pass'),
      SYSADMIN_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sysadmin_pass'),
      SMTP_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'smtp_pass'),
      SENTRY_DSN: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sentry_dsn'),
    };

    for (let i = 0; i < pUsers.length; i++) {
      drupalContainerEnv[`USERS_${i}_USER`] = pUsers[i].user.stringValue;
      drupalContainerEnv[`USERS_${i}_EMAIL`] = pUsers[i].email.stringValue;
      drupalContainerEnv[`USERS_${i}_ROLES`] = pUsers[i].roles.stringValue;
      drupalContainerSecrets[`USERS_${i}_PASS`] = ecs.Secret.fromSecretsManager(sCommonSecrets, pUsers[i].passKey);
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

      drupalContainerEnv['MATOMO_ENABLED'] = 'true';
      drupalContainerEnv['MATOMO_SITE_ID'] = pMatomoSiteId.stringValue;
      drupalContainerEnv['MATOMO_DOMAIN'] = pMatomoDomain.stringValue;
      drupalContainerEnv['MATOMO_SCRIPT_DOMAIN'] = pMatomoScriptDomain.stringValue;
      drupalContainerSecrets['MATOMO_TOKEN'] = ecs.Secret.fromSecretsManager(sCommonSecrets, 'matomo_token');
    } else {
      drupalContainerEnv['MATOMO_ENABLED'] = 'false';
      drupalContainerEnv['MATOMO_SITE_ID'] = '';
      drupalContainerEnv['MATOMO_DOMAIN'] = '';
      drupalContainerEnv['MATOMO_SCRIPT_DOMAIN'] = '';
      drupalContainerEnv['MATOMO_TOKEN'] = '';
    }

    if (props.captchaEnabled) {
      // get params
      const pRecaptchaPublicKey = ssm.StringParameter.fromStringParameterAttributes(this, 'pRecaptchaPublicKey', {
        parameterName: `/${props.environment}/opendata/common/recaptcha_public_key`,
      });

      drupalContainerEnv['CAPTCHA_ENABLED'] = 'true';
      drupalContainerEnv['RECAPTCHA_PUBLIC_KEY'] = pRecaptchaPublicKey.stringValue;
      drupalContainerSecrets['RECAPTCHA_PRIVATE_KEY'] = ecs.Secret.fromSecretsManager(sCommonSecrets, 'recaptcha_private_key');
    } else {
      drupalContainerEnv['CAPTCHA_ENABLED'] = 'false';
      drupalContainerEnv['RECAPTCHA_PUBLIC_KEY'] = '';
      drupalContainerEnv['RECAPTCHA_PRIVATE_KEY'] = '';
    }

    const drupalLogGroup = new logs.LogGroup(this, 'drupalLogGroup', {
      logGroupName: `/${props.environment}/opendata/drupal`,
    });

    const drupalContainer = drupalTaskDef.addContainer('drupal', {
      image: ecs.ContainerImage.fromEcrRepository(drupalRepo, props.envProps.DRUPAL_IMAGE_TAG),
      environment: drupalContainerEnv,
      secrets: drupalContainerSecrets,
      logging: ecs.LogDrivers.awsLogs({
        logGroup: drupalLogGroup,
        streamPrefix: 'drupal-service',
      }),
      healthCheck: {
        command: ['CMD-SHELL', 'ps -aux | grep -o "[a]pache2 -DFOREGROUND"'],
        interval: Duration.seconds(15),
        timeout: Duration.seconds(5),
        retries: 5,
        startPeriod: Duration.seconds(300),
      },
      linuxParameters: new ecs.LinuxParameters(this, 'drupalContainerLinuxParams', {
        initProcessEnabled: true,
      }),
    });

    drupalContainer.addPortMappings({
      containerPort: 80,
      protocol: ecs.Protocol.TCP,
    });

    drupalContainer.addMountPoints({
      containerPath: '/opt/drupal/web/sites/default/files',
      readOnly: false,
      sourceVolume: 'drupal_sites',
    });

    const drupalTaskPolicyAllowExec = new iam.PolicyStatement({
      actions: [
        'ssmmessages:CreateControlChannel',
        'ssmmessages:CreateDataChannel',
        'ssmmessages:OpenControlChannel',
        'ssmmessages:OpenDataChannel',
      ],
      resources: ['*'],
      effect: iam.Effect.ALLOW,
    });

    drupalTaskDef.addToTaskRolePolicy(drupalTaskPolicyAllowExec);

    this.drupalService = new ecs.FargateService(this, 'drupalService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      serviceName: "drupal",
      taskDefinition: drupalTaskDef,
      minHealthyPercent: 50,
      maxHealthyPercent: 200,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: Duration.minutes(1),
        name: 'drupal',
        container: drupalContainer,
        containerPort: 80,
      },
      enableExecuteCommand: true,
    });

    this.drupalService.connections.allowFrom(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (drupal)');
    this.drupalService.connections.allowTo(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (drupal)');
    this.drupalService.connections.allowTo(props.databaseSecurityGroup, ec2.Port.tcp(5432), 'RDS connection (drupal)');

    const drupalServiceAsg = this.drupalService.autoScaleTaskCount({
      minCapacity: props.drupalTaskDef.taskMinCapacity,
      maxCapacity: props.drupalTaskDef.taskMaxCapacity,
    });

    drupalServiceAsg.scaleOnCpuUtilization('drupalServiceAsgPolicy', {
      targetUtilizationPercent: 50,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60),
    });

    drupalServiceAsg.scaleOnMemoryUtilization('drupalServiceAsgPolicyMem', {
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

      props.migrationFileSystemProps.fileSystem.grant(drupalTaskDef.taskRole, 'elasticfilesystem:ClientRootAccess');

      drupalTaskDef.addVolume({
        name: 'ytp_files',
        efsVolumeConfiguration: {
          fileSystemId: props.migrationFileSystemProps.fileSystem.fileSystemId,
          authorizationConfig: {
            accessPointId: this.migrationFsAccessPoint.accessPointId,
          },
          transitEncryption: 'ENABLED',
        },
      });

      // NOTE: drupal storage path will be in: /mnt/ytp_files/drupal
      drupalContainer.addMountPoints({
        containerPath: '/mnt/ytp_files',
        readOnly: true,
        sourceVolume: 'ytp_files',
      });

      this.drupalService.connections.allowFrom(props.migrationFileSystemProps.securityGroup, ec2.Port.tcp(2049), 'EFS connection (drupal migrate)');
      this.drupalService.connections.allowTo(props.migrationFileSystemProps.securityGroup, ec2.Port.tcp(2049), 'EFS connection (drupal migrate)');
    }
  }
}
