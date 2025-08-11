import {Handler, S3Event} from 'aws-lambda';
import {ECSClient,RunTaskCommand} from '@aws-sdk/client-ecs';

const { CLUSTER_ID, SNS_TOPIC_ARN, TASK_DEFINITION, SUBNET_IDS, SECURITY_GROUP_ID } = process.env;

export const handler: Handler = async (event: S3Event) => {
    if(!CLUSTER_ID || !SNS_TOPIC_ARN || !TASK_DEFINITION || !SUBNET_IDS || !SECURITY_GROUP_ID) {
        return {
          statusCode: 500,
          body: 'Missing configuration values',
        }
    }

    let { bucket, object } = event.Records[0].s3

    let ecsClient = new ECSClient()
    let subnetIds = SUBNET_IDS.split(',')
    let runTaskCommand = new RunTaskCommand({
        cluster: CLUSTER_ID,
        count: 1,
        launchType: 'FARGATE',
        networkConfiguration: {
            'awsvpcConfiguration': {
                'subnets': subnetIds,
                'assignPublicIp': 'DISABLED',
                'securityGroups': [SECURITY_GROUP_ID],
            }
        },
        platformVersion: 'LATEST',
        taskDefinition: TASK_DEFINITION,
        overrides: {
            'containerOverrides': [
                {
                    'name': 'clamav-scanner',
                    'environment': [
                        {
                            'name': 'BUCKET_NAME',
                            'value': bucket.name
                        },
                        {
                            'name': 'OBJECT_KEY',
                            'value': object.key
                        },
                        {
                            'name': 'SNS_TOPIC_ARN',
                            'value': SNS_TOPIC_ARN
                        }
                    ]
                }
            ]
        }
    })
    let response = ecsClient.send(runTaskCommand)

    return response
}
