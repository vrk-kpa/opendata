import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';
import * as elb from '@aws-cdk/aws-elasticloadbalancingv2';
import * as ecsp from '@aws-cdk/aws-ecs-patterns';
import * as ssm from '@aws-cdk/aws-ssm';
import * as sm from '@aws-cdk/aws-secretsmanager';
import * as r53 from '@aws-cdk/aws-route53';
import * as acm from '@aws-cdk/aws-certificatemanager';

import { WebStackProps } from './web-stack-props';

export class WebStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props: WebStackProps) {
    super(scope, id, props);

    // get params
    const pNginxImageVersion = ssm.StringParameter.fromStringParameterAttributes(this, 'pNginxImageVersion', {
      parameterName: `/${props.environment}/opendata/nginx/image_version`,
    });
    const pNameserver = ssm.StringParameter.fromStringParameterAttributes(this, 'pNameserver', {
      parameterName: `/${props.environment}/opendata/common/nameserver`,
    });

    const nginxTaskDef = new ecs.FargateTaskDefinition(this, 'nginxTaskDef', {
      cpu: props.nginxTaskDef.taskCpu,
      memoryLimitMiB: props.nginxTaskDef.taskMem,
      volumes: [
        {
          name: 'drupal_data',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['drupal'].fileSystemId,
            rootDirectory: '/drupal_data',
          },
        },
        {
          name: 'drupal_resources',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['drupal'].fileSystemId,
            rootDirectory: '/drupal_resources',
          },
        },
        {
          name: 'ckan_resources',
          efsVolumeConfiguration: {
            fileSystemId: props.fileSystems['ckan'].fileSystemId,
            rootDirectory: '/ckan_resources',
          },
        }
      ],
    });

    // define nginx content security policies
    const nginxCspDefaultSrc: string[] = [
      '*.disquscdn.com',
      'https://disqus.com',
    ];
    const nginxCspScriptSrc: string[] = [
      'platform.twitter.com',
      'syndication.twitter.com',
      'cdn.syndication.twimg.com',
      '*.disqus.com',
      'https://disqus.com',
      '*.disquscdn.com',
      'https://www.google.com/recaptcha/',
      'https://www.gstatic.com/',
      'https://www.google.com',
      'cdn.matomo.cloud',
      'suomi.matomo.cloud',
    ];
    const nginxCspStyleSrc: string[] = [
      'https://fonts.googleapis.com',
      'https://platform.twitter.com',
      'https://ton.twimg.com',
      '*.disquscdn.com',
      'https://www.google.com',
      'https://ajax.googleapis.com',
      'https://www.gstatic.com',
    ];
    const nginxCspFrameSrc: string[] = [
      'syndication.twitter.com',
      'https://platform.twitter.com',
      'https://disqus.com',
      '*.disqus.com',
      'https://www.google.com/recaptcha/',
    ];

    const nginxContainer = nginxTaskDef.addContainer('nginx', {
      image: ecs.ContainerImage.fromEcrRepository(props.repositories['nginx'], pNginxImageVersion.stringValue),
      environment: {
        // .env.nginx
        NGINX_ROOT: '/var/www/html',
        NGINX_MAX_BODY_SIZE: '16M',
        NGINX_EXPIRES: '1h',
        NGINX_CSP_DEFAULT_SRC: nginxCspDefaultSrc.join(' '),
        NGINX_CSP_SCRIPT_SRC: nginxCspScriptSrc.join(' '),
        NGINX_CSP_STYLE_SRC: nginxCspStyleSrc.join(' '),
        NGINX_CSP_FRAME_SRC: nginxCspFrameSrc.join(' '),
        // .env
        NGINX_PORT: '80',
        DOMAIN_NAME: props.domainName,
        SECONDARY_DOMAIN_NAME: props.secondaryDomainName,
        NAMESERVER: pNameserver.stringValue,
        CKAN_HOST: `ckan.${props.namespace.namespaceName}`,
        CKAN_PORT: '5000',
        DRUPAL_HOST: `drupal.${props.namespace.namespaceName}`,
        DRUPAL_PORT: '9000',
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'nginx-service',
      }),
    });

    nginxContainer.addPortMappings({
      containerPort: 80,
      protocol: ecs.Protocol.TCP,
    });

    nginxContainer.addMountPoints({
      containerPath: '/var/www/html',
      readOnly: true,
      sourceVolume: 'drupal_data',
    }, {
      containerPath: '/var/www/drupal_resources',
      readOnly: true,
      sourceVolume: 'drupal_resources',
    }, {
      containerPath: '/var/www/ckan_resources',
      readOnly: true,
      sourceVolume: 'ckan_resources',
    });

    const nginxServiceHostedZone = r53.HostedZone.fromLookup(this, 'nginxServiceHostedZone', {
      domainName: props.fqdn,
      privateZone: false,
    });

    const nginxServiceSecondaryHostedZone = r53.HostedZone.fromLookup(this, 'nginxServiceSecondaryHostedZone', {
      domainName: props.secondaryFqdn,
      privateZone: false,
    });

    const nginxCertificate = new acm.Certificate(this, 'nginxCertificate', {
      domainName: props.domainName,
      subjectAlternativeNames: [
        props.secondaryDomainName,
      ],
      validation: acm.CertificateValidation.fromDnsMultiZone({
        [props.domainName]: nginxServiceHostedZone,
        [props.secondaryDomainName]: nginxServiceSecondaryHostedZone,
      })
    });

    const nginxService = new ecsp.ApplicationLoadBalancedFargateService(this, 'nginxService', {
      cluster: props.cluster,
      domainName: props.domainName,
      domainZone: nginxServiceHostedZone,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: cdk.Duration.minutes(1),
        name: 'nginx',
        container: nginxContainer,
        containerPort: 80,
      },
      publicLoadBalancer: true,
      protocol: elb.ApplicationProtocol.HTTPS,
      certificate: nginxCertificate,
      redirectHTTP: true,
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      taskDefinition: nginxTaskDef,
    });

    nginxService.targetGroup.configureHealthCheck({
      path: '/health',
      healthyHttpCodes: '200',
    });

    nginxService.service.connections.allowFrom(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (nginx)');
    nginxService.service.connections.allowTo(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (nginx)');
    nginxService.service.connections.allowFrom(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (nginx)');
    nginxService.service.connections.allowTo(props.fileSystems['ckan'], ec2.Port.tcp(2049), 'EFS connection (nginx)');
    nginxService.service.connections.allowFrom(props.drupalService, ec2.Port.tcp(80), 'drupal - nginx connection');
    nginxService.service.connections.allowTo(props.drupalService, ec2.Port.tcp(9000), 'nginx - drupal connection');
    nginxService.service.connections.allowFrom(props.ckanService, ec2.Port.tcp(80), 'ckan - nginx connection');
    nginxService.service.connections.allowTo(props.ckanService, ec2.Port.tcp(5000), 'nginx - ckan connection');

    const nginxServiceAsg = nginxService.service.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 4,
    });

    nginxServiceAsg.scaleOnCpuUtilization('nginxServiceAsgPolicy', {
      targetUtilizationPercent: 50,
      scaleInCooldown: cdk.Duration.minutes(1),
      scaleOutCooldown: cdk.Duration.minutes(1),
    });
  }
}
