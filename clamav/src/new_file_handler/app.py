import boto3
import os


def lambda_handler(event, context):
    s3_bucket_name = event['Records'][0]['s3']['bucket']['name']
    s3_object_key = event['Records'][0]['s3']['object']['key']

    vpc_id = os.getenv('VPC_ID')
    sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
    vpc = boto3.resource('ec2').Vpc(vpc_id)
    private_subnet_filter = [{'Values': ['private'], 'Name': 'tag:Reach'}]
    private_subnets = vpc.subnets.filter(Filters=private_subnet_filter)
    private_subnet_ids = [subnet.id for subnet in private_subnets]

    client = boto3.client('ecs')
    response = client.run_task(
        cluster='clamav-scanner-cluster',
        count=1,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': private_subnet_ids,
                'assignPublicIp': 'DISABLED'
            }
        },
        platformVersion='LATEST',
        taskDefinition='clamav-scanner',
        overrides={
            'containerOverrides': [
                {
                    'name': 'clamav-scanner',
                    'environment': [
                        {
                            'name': 'BUCKET_NAME',
                            'value': s3_bucket_name
                        },
                        {
                            'name': 'OBJECT_KEY',
                            'value': s3_object_key
                        },
                        {
                            'name': 'SNS_TOPIC_ARN',
                            'value': sns_topic_arn
                        }
                    ]
                }
            ]
        }
    )

    return str(response)
