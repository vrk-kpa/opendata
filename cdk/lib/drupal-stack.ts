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

import { DrupalStackProps } from './drupal-stack-props';
import { DrupalUser } from './drupal-user';

export class DrupalStack extends cdk.Stack {
  readonly drupalFsDataAccessPoint: efs.IAccessPoint;
  readonly drupalFsResourcesAccessPoint: efs.IAccessPoint;
  readonly drupalService: ecs.FargateService;

  constructor(scope: cdk.Construct, id: string, props: DrupalStackProps) {
    super(scope, id, props);

    // get params
    const pDrupalImageVersion = ssm.StringParameter.fromStringParameterAttributes(this, 'pDrupalImageVersion', {
      parameterName: `/${props.environment}/opendata/drupal/image_version`,
    });
    const pDbHost = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbHost', {
      parameterName: `/${props.environment}/opendata/common/db_host`,
    });
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
    const pUsers: DrupalUser[] = [
      new DrupalUser(this, props.environment, 0),
      new DrupalUser(this, props.environment, 1),
      new DrupalUser(this, props.environment, 2),
    ];

    // get secrets
    const sDrupalSecrets = sm.Secret.fromSecretNameV2(this, 'sDrupalSecrets', `/${props.environment}/opendata/drupal`);
    const sCommonSecrets = sm.Secret.fromSecretNameV2(this, 'sCommonSecrets', `/${props.environment}/opendata/common`);

    this.drupalFsDataAccessPoint = props.fileSystems['drupal'].addAccessPoint('drupalFsDataAccessPoint', {
      path: '/drupal_data',
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
    
    this.drupalFsResourcesAccessPoint = props.fileSystems['drupal'].addAccessPoint('drupalFsResourcesAccessPoint', {
      path: '/drupal_resources',
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
          name: 'drupal_data',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['drupal'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.drupalFsDataAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        }, 
        {
          name: 'drupal_resources',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['drupal'].fileSystemId,
            authorizationConfig: {
              accessPointId: this.drupalFsResourcesAccessPoint.accessPointId,
            },
            transitEncryption: 'ENABLED',
          },
        }
      ],
    });

    props.fileSystems['drupal'].grant(drupalTaskDef.taskRole, 'elasticfilesystem:ClientRootAccess');

    let drupalContainerEnv: { [key: string]: string; } = {
      // .env.drupal
      DRUPAL_IMAGE_VERSION: pDrupalImageVersion.stringValue,
      DRUPAL_CONFIG_SYNC_DIRECTORY: '/opt/drupal/web/sites/default/sync',
      // .env
      DB_HOST: pDbHost.stringValue,
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
      USERS_0_USER: pUsers[0].user.stringValue,
      USERS_0_EMAIL: pUsers[0].email.stringValue,
      USERS_0_ROLES: pUsers[0].roles.stringValue,
      USERS_1_USER: pUsers[1].user.stringValue,
      USERS_1_EMAIL: pUsers[1].email.stringValue,
      USERS_1_ROLES: pUsers[1].roles.stringValue,
      USERS_2_USER: pUsers[2].user.stringValue,
      USERS_2_EMAIL: pUsers[2].email.stringValue,
      USERS_2_ROLES: pUsers[2].roles.stringValue,
    };

    let drupalContainerSecrets: { [key: string]: ecs.Secret; } = {
      // .env.drupal
      DRUPAL_HASH_SALT: ecs.Secret.fromSecretsManager(sDrupalSecrets, 'drupal_hash_salt'),
      // .env
      DB_DRUPAL_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'db_drupal_pass'),
      SYSADMIN_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'sysadmin_pass'),
      SMTP_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, 'smtp_pass'),
      USERS_0_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, pUsers[0].passKey),
      USERS_1_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, pUsers[1].passKey),
      USERS_2_PASS: ecs.Secret.fromSecretsManager(sCommonSecrets, pUsers[2].passKey),
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

    const drupalContainer = drupalTaskDef.addContainer('drupal', {
      image: ecs.ContainerImage.fromEcrRepository(props.repositories['drupal'], pDrupalImageVersion.stringValue),
      environment: drupalContainerEnv,
      secrets: drupalContainerSecrets,
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'drupal-service',
      }),
    });

    drupalContainer.addPortMappings({
      containerPort: 9000,
      protocol: ecs.Protocol.TCP,
    });

    drupalContainer.addMountPoints({
      containerPath: '/opt/drupal/web',
      readOnly: false,
      sourceVolume: 'drupal_data',
    }, {
      containerPath: '/var/www/resources',
      readOnly: false,
      sourceVolume: 'drupal_resources',
    });

    this.drupalService = new ecs.FargateService(this, 'drupalService', {
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      cluster: props.cluster,
      taskDefinition: drupalTaskDef,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: cdk.Duration.minutes(1),
        name: 'drupal',
        container: drupalContainer,
        containerPort: 9000,
      },
    });

    this.drupalService.connections.allowFrom(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (drupal)');
    this.drupalService.connections.allowTo(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (drupal)');
    this.drupalService.connections.allowTo(props.databaseSecurityGroup, ec2.Port.tcp(5432), 'RDS connection (drupal)');

    const drupalServiceAsg = this.drupalService.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: 2,
    });

    drupalServiceAsg.scaleOnCpuUtilization('drupalServiceAsgPolicy', {
      targetUtilizationPercent: 50,
      scaleInCooldown: cdk.Duration.seconds(150),
      scaleOutCooldown: cdk.Duration.seconds(150),
    });
  }
}
