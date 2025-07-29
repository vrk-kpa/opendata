import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as sd from 'aws-cdk-lib/aws-servicediscovery';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as ecsp from 'aws-cdk-lib/aws-ecs-patterns';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as r53 from 'aws-cdk-lib/aws-route53';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

import { WebStackProps } from './web-stack-props';
import { parseEcrAccountId, parseEcrRegion } from './common-stack-funcs';

export class WebStack extends Stack {
  constructor(scope: Construct, id: string, props: WebStackProps) {
    super(scope, id, props);

    // get params
    const pNameserver = ssm.StringParameter.fromStringParameterAttributes(this, 'pNameserver', {
      parameterName: `/${props.environment}/opendata/common/nameserver`,
    });

    // get repositories
    const nginxRepo = ecr.Repository.fromRepositoryArn(this, 'nginxRepo', `arn:aws:ecr:${parseEcrRegion(props.envProps.REGISTRY)}:${parseEcrAccountId(props.envProps.REGISTRY)}:repository/${props.envProps.REPOSITORY}/nginx`);

    const nginxTaskDef = new ecs.FargateTaskDefinition(this, 'nginxTaskDef', {
      cpu: props.nginxTaskDef.taskCpu,
      memoryLimitMiB: props.nginxTaskDef.taskMem,
      volumes: [
        {
          name: 'nginx_tmp_tmpfs',
          dockerVolumeConfiguration: {
            scope: ecs.Scope.TASK,
            driver: "tmpfs",
            driverOpts: {
              'type': 'tmpfs',
              'device': 'tmpfs',
              'o': 'exec,mode=1777'
            }
          }
        },
      ]
    });

    // define nginx content security policies
    const nginxCspDefaultSrc: string[] = [];
    const nginxCspScriptSrc: string[] = [
      'https://www.google.com/recaptcha/',
      'https://www.gstatic.com/',
      'https://www.google.com',
      'cdn.matomo.cloud',
      'suomi.matomo.cloud',
      'https://js-de.sentry-cdn.com',
      'https://browser.sentry-cdn.com',
      'cdn.jsdelivr.net'
    ];
    const nginxCspStyleSrc: string[] = [
      'https://fonts.googleapis.com',
      'https://www.google.com',
      'https://ajax.googleapis.com',
      'https://www.gstatic.com',
      'cdn.jsdelivr.net'
    ];
    const nginxCspFrameSrc: string[] = [
      'https://www.google.com/recaptcha/',
      'https://avoindata-' + props.environment + '-datasets.s3.eu-west-1.amazonaws.com/'
    ];

    const nginxCspConnectSrc: string[] = [
      "suomi.matomo.cloud",
      "*.sentry.io"
    ]

    const nginxCspFontSrc: string[] = [
      "https://themes.googleusercontent.com",
      "https://fonts.gstatic.com",
      "cdn.jsdelivr.net"
    ]

    const nginxLogGroup = new logs.LogGroup(this, 'nginxLogGroup', {
      logGroupName: `/${props.environment}/opendata/nginx`,
    });

    const nginxContainer = nginxTaskDef.addContainer('nginx', {
      image: ecs.ContainerImage.fromEcrRepository(nginxRepo, props.envProps.NGINX_IMAGE_TAG),
      environment: {
        // .env.nginx
        NGINX_ROOT: '/var/www/html',
        NGINX_MAX_BODY_SIZE: '5000M',
        NGINX_EXPIRES: '1h',
        NGINX_CSP_DEFAULT_SRC: nginxCspDefaultSrc.join(' '),
        NGINX_CSP_SCRIPT_SRC: nginxCspScriptSrc.join(' '),
        NGINX_CSP_STYLE_SRC: nginxCspStyleSrc.join(' '),
        NGINX_CSP_FRAME_SRC: nginxCspFrameSrc.join(' '),
        NGINX_CSP_CONNECT_SRC: nginxCspConnectSrc.join(' '),
        NGINX_CSP_FONT_SRC: nginxCspFontSrc.join(' '),
        // .env
        NGINX_PORT: '80',
        DOMAIN_NAME: props.domainName,
        SECONDARY_DOMAIN_NAME: props.secondaryDomainName,
        BASE_DOMAIN_NAME: props.fqdn,
        SECONDARY_BASE_DOMAIN_NAME: props.secondaryFqdn,
        NAMESERVER: pNameserver.stringValue,
        CKAN_HOST: `ckan.${props.namespace.namespaceName}`,
        CKAN_PORT: '5000',
        DRUPAL_HOST: `drupal.${props.namespace.namespaceName}`,
        DRUPAL_PORT: '80',
        NGINX_ROBOTS_ALLOW: props.allowRobots,
      },
      logging: ecs.LogDrivers.awsLogs({
        logGroup: nginxLogGroup,
        streamPrefix: 'nginx-service',
      }),
      readonlyRootFilesystem: true
    });

    nginxContainer.addPortMappings({
      containerPort: 80,
      protocol: ecs.Protocol.TCP,
    });

    nginxContainer.addMountPoints({
      containerPath: '/tmp',
      readOnly: false,
      sourceVolume: 'nginx_tmp_tmpfs',
    });

    const nginxServiceHostedZone = r53.HostedZone.fromLookup(this, 'nginxServiceHostedZone', {
      domainName: props.fqdn,
      privateZone: false,
    });

    const nginxServiceSecondaryHostedZone = r53.HostedZone.fromLookup(this, 'nginxServiceSecondaryHostedZone', {
      domainName: props.secondaryFqdn,
      privateZone: false,
    });


    let nginxService: ecsp.ApplicationLoadBalancedFargateService | null = null;

    nginxService = new ecsp.ApplicationLoadBalancedFargateService(this, 'nginxService', {
      cluster: props.cluster,
      cloudMapOptions: {
        cloudMapNamespace: props.namespace,
        dnsRecordType: sd.DnsRecordType.A,
        dnsTtl: Duration.minutes(1),
        name: 'nginx',
        container: nginxContainer,
        containerPort: 80,
      },
      publicLoadBalancer: true,
      protocol: elb.ApplicationProtocol.HTTPS,
      certificate: props.certificate,
      redirectHTTP: false,
      platformVersion: ecs.FargatePlatformVersion.VERSION1_4,
      taskDefinition: nginxTaskDef,
      minHealthyPercent: 50,
      maxHealthyPercent: 200,
      loadBalancer: props.loadBalancer,
      openListener: false
    });


    nginxService.targetGroup.configureHealthCheck({
      path: '/health',
      healthyHttpCodes: '200',
    });

    nginxService.targetGroup.setAttribute('deregistration_delay.timeout_seconds', '60');

    nginxService.service.connections.allowFrom(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (nginx)');
    nginxService.service.connections.allowTo(props.fileSystems['drupal'], ec2.Port.tcp(2049), 'EFS connection (nginx)');
    nginxService.service.connections.allowFrom(props.drupalService, ec2.Port.tcp(80), 'drupal - nginx connection');
    nginxService.service.connections.allowTo(props.drupalService, ec2.Port.tcp(80), 'nginx - drupal connection');
    nginxService.service.connections.allowFrom(props.ckanService, ec2.Port.tcp(80), 'ckan - nginx connection');
    nginxService.service.connections.allowTo(props.ckanService, ec2.Port.tcp(5000), 'nginx - ckan connection');

    props.ckanService.connections.allowTo(props.drupalService, ec2.Port.tcp(80), 'ckan - drupal connection')
    props.ckanService.connections.allowFrom(props.drupalService, ec2.Port.tcp(5000), 'drupal - ckan connection')


    const nginxServiceAsg = nginxService.service.autoScaleTaskCount({
      minCapacity: props.nginxTaskDef.taskMinCapacity,
      maxCapacity: props.nginxTaskDef.taskMaxCapacity,
    });

    nginxServiceAsg.scaleOnCpuUtilization('nginxServiceAsgPolicy', {
      targetUtilizationPercent: 50,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60),
    });
  }
}
