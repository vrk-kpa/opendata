import { Fn, Stack,
         aws_ecr as ecr,
         aws_ecs as ecs,
         aws_s3 as s3,
         aws_logs as logs,
         aws_s3_notifications as s3n,
         aws_lambda_nodejs as lambdaNodejs
       } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ClamavScannerStackProps } from './clamav-scanner-stack-props';
import { parseEcrAccountId, parseEcrRegion } from './common-stack-funcs';
import { ClamavScan } from './clamav-scan';
import { Port, SecurityGroup } from 'aws-cdk-lib/aws-ec2';

export class ClamavScannerStack extends Stack {

  readonly lambda: lambdaNodejs.NodejsFunction;

  constructor(scope: Construct, id: string, props: ClamavScannerStackProps) {
    super(scope, id, props);

    const clamavRepo = ecr.Repository.fromRepositoryArn(this, 'clamavRepo', `arn:aws:ecr:${parseEcrRegion(props.envProps.REGISTRY)}:${parseEcrAccountId(props.envProps.REGISTRY)}:repository/${props.envProps.REPOSITORY}/clamav`);

    const clamavTaskDef = new ecs.FargateTaskDefinition(this, 'clamavTaskDef', {
      cpu: props.clamavTaskDef.taskCpu,
      memoryLimitMiB: props.clamavTaskDef.taskMem,
    });

    const clamavLogGroup = new logs.LogGroup(this, 'clamavLogGroup', {
      logGroupName: `/${props.environment}/opendata/clamav`,
    });
    const clamavContainer = clamavTaskDef.addContainer('clamav', {
      image: ecs.ContainerImage.fromEcrRepository(clamavRepo, props.envProps.CLAMAV_IMAGE_TAG),
      containerName: "clamav-scanner",
      logging: ecs.LogDrivers.awsLogs({
        logGroup: clamavLogGroup,
        streamPrefix: "clamav"
      }),
    });


    const clamavFileSystemAccessPoint = props.clamavFileSystem.addAccessPoint('clamavFileSystemAccessPoint', {
      path: '/clamav',
      createAcl: {
        ownerGid: '101',
        ownerUid: '100',
        permissions: '0755',
      },
    })
    clamavTaskDef.addVolume({
      name: 'clamav_files',
      efsVolumeConfiguration: {
        fileSystemId: props.clamavFileSystem.fileSystemId,
        authorizationConfig: {
          accessPointId: clamavFileSystemAccessPoint.accessPointId,
        },
        transitEncryption: 'ENABLED',
      },
    });

    clamavContainer.addMountPoints({
      containerPath: '/var/lib/clamav',
      readOnly: false,
      sourceVolume: 'clamav_files',
    });

    const clamavSecurityGroup = new SecurityGroup(this, 'clamav-security-group', {
      vpc: props.cluster.vpc,
      description: "clamav container security group"
    });
    clamavSecurityGroup.connections.allowTo(props.clamavFileSystem, Port.tcp(2049), 'EFS connection (clamav)')
    const privateSubnetA = Fn.importValue('vpc-SubnetPrivateA')
    const privateSubnetB = Fn.importValue('vpc-SubnetPrivateB')

    const clamavScan = new ClamavScan(this, 'clamavScan', {
      environment: props.environment,
      cluster: props.cluster,
      task: clamavTaskDef,
      snsTopic: props.topic,
      subnetIds: [privateSubnetA, privateSubnetB],
      securityGroup: clamavSecurityGroup,
    })

    // Allow clamavScan lambda to run the ecs task
    clamavTaskDef.grantRun(clamavScan.lambda);

    // Allow clamavScan to publish on the SNS topic
    props.topic.grantPublish(clamavTaskDef.taskRole)

    // Allow clamavScan to manage S3 files
    const bucket = s3.Bucket.fromBucketName(this, 'DatasetBucket', props.datasetBucketName);
    bucket.grantReadWrite(clamavTaskDef.taskRole);
    // S3 events to clamavScan lambda
    bucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.LambdaDestination(clamavScan.lambda))
  }
}

