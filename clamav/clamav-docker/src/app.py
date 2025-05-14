from clamscan import ClamScanner
import datetime
import logging
import boto3
from botocore.exceptions import ClientError
import hashlib
import tempfile
import json
import os
import sys

logging.basicConfig(format='%(name)-12s: %(levelname)-8s %(message)s',
                    level=logging.INFO, stream=sys.stdout)

logger = logging.getLogger(__name__)


def main():
    s3_bucket = os.getenv('BUCKET_NAME')
    object_key = os.getenv('OBJECT_KEY')
    sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
    s3 = boto3.client('s3')
    set_object_tags(s3, s3_bucket, object_key, updated=datetime.datetime.utcnow().isoformat())
    sns = boto3.client('sns')
    processed_file = tempfile.NamedTemporaryFile(delete=False)

    try:
        s3.download_file(s3_bucket, object_key, processed_file.name)

    except ClientError as e:
        logger.error(f'Downloading {object_key} from {s3_bucket} failed: \n{e}')
        raise e

    target_file_hash = get_sha256(processed_file.name)
    set_object_tags(s3, s3_bucket, object_key, updated=datetime.datetime.utcnow().isoformat(), sha256=target_file_hash)

    if os.stat(processed_file.name).st_size == 0:
        logger.info("Empty file, skipping scan...")
        return

    clamscanner = ClamScanner(processed_file.name)
    scan_output = clamscanner.scan_file()
    errors = {error for status, error in scan_output.values() if status == 'ERROR'}
    infections = {virus for status, virus in scan_output.values() if status == 'FOUND'}

    if errors:
        error_str = ', '.join(errors)
        raise RuntimeError(f'Error processing {object_key}: {error_str}')

    if infections:
        infection_name = ','.join(infections)
        logger.info(f'{object_key} is infected with {infection_name}')
        now = datetime.datetime.utcnow().isoformat()
        set_object_tags(s3, s3_bucket, object_key, malware=f'infected {infection_name}', updated=now, sha256=target_file_hash)
        replace_object_with_empty_file(s3, s3_bucket, object_key)
        set_object_tags(s3, s3_bucket, object_key, malware=f'infected {infection_name}', updated=now, sha256=target_file_hash)
        sns_publish(sns, sns_topic_arn,  s3_bucket, object_key, infection_name)
    else:
        logger.info(f'{object_key} is clean')
        now = datetime.datetime.utcnow().isoformat()
        set_object_tags(s3, s3_bucket, object_key, malware='clean', updated=now, sha256=target_file_hash)


def get_sha256(filename):
    sha256_hash = hashlib.sha256()
    try:
        with open(filename, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
            logger.info(f'Calculated sha256: {sha256_hash.hexdigest()}')
            return (sha256_hash.hexdigest())
    except OSError as e:
        logger.error(f'Opening file {filename}: \n{e}')
        raise e


def set_object_tags(client, bucket, key, **new_tags):

    try:
        client.put_object_tagging(
            Bucket=bucket,
            Key=key,
            Tagging={
                'TagSet': [{'Key': str(k)[:128], 'Value': str(v)[:256]} for k, v in new_tags.items()]
            }
        )
    except Exception as e:
        logger.error(
            f'Tagging object {key} failed: \n{e}')
        raise e


def replace_object_with_empty_file(client, bucket, key):

    try:
        logger.info(
            f'Replacing object {key} in {bucket} with empty file')
        # Delete is not needed but if S3 versioning is used it adds delete marker for clarity
        client.delete_object(Bucket=bucket, Key=key)
        client.put_object(Bucket=bucket, Key=key, Body=b'')
        logger.info(f'Object {key} replaced')
    except Exception as e:
        logger.error(
            f'Replacing object failed for {key}: \n{e}')
        raise e


def sns_publish(sns_client, sns_topic_arn,  bucket, key, infection_name):
    message = {
        "bucket_name": bucket,
        "object_key": key,
        "infection_name": infection_name
    }

    try:
        sns_client.publish(
            Subject='Virus found',
            TopicArn=sns_topic_arn,
            Message=json.dumps(message)
        )
        logger.info('Message published to SNS')
    except ClientError as e:
        logger.error(f'Message publishing failed: \n{e}')


if __name__ == '__main__':
    main()
