import requests
import boto3
import json
import os


def lambda_handler(event, context):

    slack_channel = os.getenv('SLACK_CHANNEL')
    slack_user = os.getenv('SLACK_USER')
    slack_path = os.getenv('SLACK_PATH')
    slack_url = f'https://hooks.slack.com{slack_path}'

    severity = "bad"
    message = event['Records'][0]['Sns']['Message']
    message_json = json.loads(message)
    subject = event['Records'][0]['Sns']['Subject']

    fields = [
        {
            "title": "Bucket",
            "value": message_json['bucket_name'],
            "short": True
        }, {
            "title": "Object key",
            "value": message_json['object_key'],
            "short": True
        }, {
            "title": "Infection name",
            "value": message_json['infection_name'],
            "short": True
        }
    ]

    post_data = {
        "channel": slack_channel,
        "username": slack_user,
        "icon_emoji": ":clamav:",
        "attachments": [
            {
                "color": severity,
                "fallback": message,
                "title": subject,
                "fields": fields
            }
        ]
    }

    response = requests.post(slack_url, data=json.dumps(post_data))

    return str(response)
