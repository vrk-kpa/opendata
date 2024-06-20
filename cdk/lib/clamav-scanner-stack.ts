import { Fn, Stack,
         aws_ecr as ecr,
         aws_ecs as ecs,
         aws_iam as iam,
         aws_ssm as ssm,
         aws_s3 as s3,
         aws_s3_notifications as s3n,
         aws_lambda_nodejs as lambdaNodejs
       } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ClamavScannerStackProps } from './clamav-scanner-stack-props';
import { parseEcrAccountId, parseEcrRegion } from './common-stack-funcs';
import { ClamavScan } from './clamav-scan';

export class ClamavScannerStack extends Stack {

  readonly lambda: lambdaNodejs.NodejsFunction;

  constructor(scope: Construct, id: string, props: ClamavScannerStackProps) {
    super(scope, id, props);

    const clamavRepo = ecr.Repository.fromRepositoryArn(this, 'clamavRepo', `arn:aws:ecr:${parseEcrRegion(props.envProps.REGISTRY)}:${parseEcrAccountId(props.envProps.REGISTRY)}:repository/${props.envProps.REPOSITORY}/clamav`);

    const clamavTaskDef = new ecs.FargateTaskDefinition(this, 'clamavTaskDef', {
      cpu: props.clamavTaskDef.taskCpu,
      memoryLimitMiB: props.clamavTaskDef.taskMem,
    });

    // Allow clamavScan to manage S3 files
    const pCkanCloudstorageContainerName = ssm.StringParameter.fromStringParameterAttributes(this, 'pCkanCloudstorageContainerName', {
      parameterName: `/${props.environment}/opendata/ckan/cloudstorage_container_name`,
    });
    const bucketArn = `arn:aws:s3:::${pCkanCloudstorageContainerName.stringValue}`;

    const clamavScanPolicyAllowCloudstorage = new iam.PolicyStatement({
      actions: [
                  "s3:DeleteObject",
                  "s3:DeleteObjectTagging",
                  "s3:GetObject",
                  "s3:GetObjectTagging",
                  "s3:HeadBucket",
                  "s3:ListObjects",
                  "s3:PutObject",
                  "s3:PutObjectTagging",
                ],
      resources: [
        bucketArn,
        `${bucketArn}/*`,
      ],
      effect: iam.Effect.ALLOW,
    });

    clamavTaskDef.addToTaskRolePolicy(clamavScanPolicyAllowCloudstorage)

    const clamavContainer = clamavTaskDef.addContainer('clamav', {
      image: ecs.ContainerImage.fromEcrRepository(clamavRepo, props.envProps.CLAMAV_IMAGE_TAG),
    });

    const privateSubnetA = Fn.importValue('vpc-SubnetPrivateA')
    const privateSubnetB = Fn.importValue('vpc-SubnetPrivateB')

    const clamavScan = new ClamavScan(this, 'clamavScan', {
      environment: props.environment,
      cluster: props.cluster,
      task: clamavTaskDef,
      snsTopic: props.topic,
      subnetIds: [privateSubnetA, privateSubnetB]
    })

    // S3 events to clamavScan lambda
    const bucket = s3.Bucket.fromBucketArn(this, 'bucket', bucketArn);
    bucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.LambdaDestination(clamavScan.lambda))
  }
}

