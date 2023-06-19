import { Stack } from 'aws-cdk-lib';
import { MonitoringStackProps } from './monitoring-stack-props';

import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaNodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as assertions from 'aws-cdk-lib/assertions';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as logs from 'aws-cdk-lib/aws-logs';

import * as path from 'path';
import { Construct } from 'constructs';

export class MonitoringStack extends Stack {
  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    // Task restart zulip reporting
    const zulipSecret = new sm.Secret(this, `/${props.environment}/opendata/common/zulip_api_key`);
  
    const sendToDeveloperZulip = new lambdaNodejs.NodejsFunction(this, "sendToDeveloperZulipLambda", {
      runtime: lambda.Runtime.NODEJS_18_X,
      entry: path.join(__dirname, `/../functions/zulip.ts`),
      handler: "sendToZulip",
      environment: {
        ZULIP_API_USER: 'avoindata-bot@turina.dvv.fi',
        ZULIP_API_KEY_SECRET: zulipSecret.secretName,
        ZULIP_API_URL: 'https://turina.dvv.fi',
        ZULIP_STREAM: 'avoindata.fi',
        ZULIP_TOPIC: 'Container restarts'
      }
    });

    zulipSecret.grantRead(sendToDeveloperZulip);
    
    // Task health check failure log group
    const taskHealthCheckFailLogGroup = new logs.LogGroup(this, 'taskHealthCheckFailedGroup', {
      logGroupName: 'taskHealthCheckFailedGroup'
    });

    // Eventbridge rule to send 
    const sendToDeveloperZulipTarget = new eventsTargets.LambdaFunction(sendToDeveloperZulip, {});
    const taskHealthCheckFailLogGroupTarget = new eventsTargets.CloudWatchLogGroup(taskHealthCheckFailLogGroup);
    const taskHealthCheckFailedRule = new events.Rule(this, 'taskHealthCheckFailedRule', {
      description: 'Rule for forwarding container health check failures to zulip',
      eventPattern: {
        source: ['aws.ecs'],
        detail: {
          message: assertions.Match.stringLikeRegexp('service [^ ]+ task [0-9a-f]+ failed container health checks.')
        }
      },
      targets: [sendToDeveloperZulipTarget, taskHealthCheckFailLogGroupTarget],
    })

  }
}

