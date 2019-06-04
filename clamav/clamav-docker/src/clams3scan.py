from sys import stdout
from botocore.exceptions import ClientError
import boto3
import clamd
import json
import logging
import os
import subprocess
import time

logger = logging.getLogger(__name__)


def clamd_check(decorated):
    def wrapper(*args):
        while not args[0].clamd_up:
            try:
                args[0].clamd_client.ping()
            except:
                time.sleep(5)
        return decorated(*args)
    return wrapper

class ClamS3Scanner:
    clamd_up = False
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')
    clamd_client = clamd.ClamdUnixSocket()

    def __init__(self, s3_bucket, object_key, sns_topic_arn=None):
        self.s3_bucket = s3_bucket
        self.object_key = object_key
        self.s3_object_client = boto3.resource(
            's3').Object(s3_bucket, object_key)
        self.sns_topic_arn = sns_topic_arn
        self.update_clamav_definitions()
        self.start_clam_daemon()

    @staticmethod
    def update_clamav_definitions():
        try:
            logger.info('Updating ClamAV database')
            freshclam_process_output = subprocess.check_output(
                'freshclam').decode('utf-8')
            if 'Database updated' in freshclam_process_output:
                logger.info('ClamAV database updated')
            elif freshclam_process_output.count('is up to date') >= 3:
                logger.info('ClamAV database is up to date')
            else:
                raise Exception(
                    f'Unable to ensure that ClamAV database is up to date: \n{freshclam_process_output}')
        except subprocess.CalledProcessError as e:
            logger.error(f'ClamAV database update failed: \n{e.output}')
            raise e

    def start_clam_daemon(self):
        clamd_max_retry_count = 12
        clamd_retry_count = 0

        subprocess.Popen(['clamd'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        while not (self.clamd_up):
            try:
                self.clamd_client.ping()
                logger.info('Clamd is up')
                self.clamd_up = True
            except:
                if clamd_retry_count == 12:
                    raise Exception(
                        f'Clamd failed to respond within {clamd_max_retry_count} retries')
                logger.warning('Clamd is not up yet, retrying in 10 seconds')
                time.sleep(10)
                clamd_retry_count += 1

    @clamd_check
    def scan_file(self):
        try:
            file_name = self.object_key.split('/')[-1]
            scan_target_path = f'/tmp/{file_name}'
            self.s3_object_client.download_file(scan_target_path)
            logger.info(
                f'Starting scan of {self.object_key} in {self.s3_bucket}')
            scan_output = self.clamd_client.scan(scan_target_path)
            return scan_output
        except ClientError as e:
            logger.error(
                f'Downloading {self.object_key} from {self.s3_bucket} failed: \n{e}')
            raise e
        except clamd.ClamdError as e:
            logger.error(f'Clamd scan failed: \n{e}')
            raise e

    def sns_publish(self, infection_name):
        message = {
            "bucket_name": self.s3_bucket,
            "object_key": self.object_key,
            "infection_name": infection_name
        }

        try:
            self.sns_client.publish(
                Subject='Virus found',
                TopicArn=self.sns_topic_arn,
                Message=json.dumps(message)
            )
            logger.info('Message published to SNS')
        except ClientError as e:
            logger.error(f'Message publishing failed: \n{e}')

    def tag_object(self, tag_value):
        s3_tags = {
            'TagSet': [
                {
                    'Key': 'Status',
                    'Value': tag_value
                }
            ]
        }

        try:
            self.s3_client.put_object_tagging(
                Bucket=self.s3_bucket, Key=self.object_key, Tagging=s3_tags)
            logger.info(f'Tagged {self.object_key} with Status: {tag_value}')
        except ClientError as e:
            logger.error(f'Object tagging failed: \n{e}')
            raise e

    def delete_object(self):
        try:
            logger.info(
                f'Setting delete marker for {self.object_key} in {self.s3_bucket}')
            self.s3_object_client.delete()
            logger.info(f'Delete marker set for {self.object_key}')
        except Exception as e:
            logger.error(
                f'Delete marker setting failed for {self.object_key}: \n{e}')
            raise e
