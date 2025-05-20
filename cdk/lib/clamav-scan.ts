import { aws_lambda as lambda,
         aws_lambda_nodejs as lambda_nodejs
       } from 'aws-cdk-lib';
import {Construct} from "constructs";
import {ClamavScanProps} from "./clamav-scan-props";

export class ClamavScan extends Construct {
  readonly lambda: lambda_nodejs.NodejsFunction;
  constructor(scope: Construct, id: string, props: ClamavScanProps) {
    super(scope, id);

    this.lambda = new lambda_nodejs.NodejsFunction(this, 'function', {
      environment: {
        CLUSTER_ID: props.cluster.clusterArn,
        SNS_TOPIC_ARN: props.snsTopic.topicArn,
        TASK_DEFINITION: props.task.taskDefinitionArn,
        SUBNET_IDS: props.subnetIds.join(","),
        SECURITY_GROUP_ID: props.securityGroup.securityGroupId,
      },
      runtime: lambda.Runtime.NODEJS_20_X,
    });
  }
}
