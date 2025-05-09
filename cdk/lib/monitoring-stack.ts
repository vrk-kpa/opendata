import { Stack,
         aws_events as events,
         aws_events_targets as eventsTargets,
         aws_logs as logs
       } from 'aws-cdk-lib';
import { MonitoringStackProps } from './monitoring-stack-props';
import { Construct } from 'constructs';

export class MonitoringStack extends Stack {
  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    // Task health check failure log group
    const taskHealthCheckFailLogGroup = new logs.LogGroup(this, 'taskHealthCheckFailedGroup', {
      logGroupName: 'taskHealthCheckFailedGroup'
    });

    // Eventbridge rule to send 
    const sendToDeveloperZulipTarget = new eventsTargets.SnsTopic(props.sendToZulipTopic, {});
    const taskHealthCheckFailLogGroupTarget = new eventsTargets.CloudWatchLogGroup(taskHealthCheckFailLogGroup);

    new events.Rule(this, 'taskHealthCheckFailedRule', {
      description: 'Rule for forwarding container health check failures to zulip',
      eventPattern: {
        source: ['aws.ecs'],
        detail: {
          desiredStatus: ['STOPPED'],
          stoppedReason: [{wildcard: '*health*'}]
        }
      },
      targets: [sendToDeveloperZulipTarget, taskHealthCheckFailLogGroupTarget],
    })

  }
}

