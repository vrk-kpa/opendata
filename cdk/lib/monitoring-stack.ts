import { Stack } from 'aws-cdk-lib';
import { MonitoringStackProps } from './monitoring-stack-props';

import * as events from 'aws-cdk-lib/aws-events';
import * as assertions from 'aws-cdk-lib/assertions';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as logs from 'aws-cdk-lib/aws-logs';

import { Construct } from 'constructs';

export class MonitoringStack extends Stack {
  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    // Task health check failure log group
    const taskHealthCheckFailLogGroup = new logs.LogGroup(this, 'taskHealthCheckFailedGroup', {
      logGroupName: 'taskHealthCheckFailedGroup'
    });

    // Eventbridge rule to send 
    const sendToDeveloperZulipTarget = new eventsTargets.LambdaFunction(props.sendToZulipLambda, {});
    const taskHealthCheckFailLogGroupTarget = new eventsTargets.CloudWatchLogGroup(taskHealthCheckFailLogGroup);

    new events.Rule(this, 'taskHealthCheckFailedRule', {
      description: 'Rule for forwarding container health check failures to zulip',
      eventPattern: {
        source: ['aws.ecs'],
        detail: {
          message: [{suffix: 'failed container health checks.'}]
        }
      },
      targets: [sendToDeveloperZulipTarget, taskHealthCheckFailLogGroupTarget],
    })

  }
}

