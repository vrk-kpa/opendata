from sys import stdout
import boto3
import clamd
import logging
import os
import subprocess
import time

s3_bucket = os.getenv('BUCKET_NAME')
object_key = os.getenv('OBJECT_KEY')
file_name = object_key.split('/')[-1]

s3object = boto3.resource('s3').Object(s3_bucket, object_key)
s3client = boto3.client('s3')

logger = logging.getLogger('clamavscanner')
logger.setLevel(logging.INFO)
logformatter = logging.Formatter(
    '%(name)-12s: %(levelname)-8s %(message)s')
loghandler = logging.StreamHandler(stdout)
loghandler.setFormatter(logformatter)
logger.addHandler(loghandler)


def tag_object(s3_bucket, object_key, tag_value):
    s3_tags = {
        'TagSet': [
            {
                'Key': 'Status',
                'Value': tag_value
            }
        ]
    }

    s3client.put_object_tagging(
        Bucket=s3_bucket, Key=object_key, Tagging=s3_tags)
    logger.info('Tagged {} with Status: {}'.format(object_key, tag_value))


def delete_object(s3_bucket, object_key):
    s3object.delete()
    logger.info('Delete marker set for {}'.format(object_key))


def update_clamav_definitions():
    try:
        logger.info('Updating ClamAV database')
        freshclam_process_output = subprocess.check_output(
            'freshclam').decode('utf-8').split('\n')
        if (any('Database updated') in line for line in freshclam_process_output):
            logger.info('ClamAV database updated')
    except freshclam_process_output as e:
        logger.error('ClamAV database update failed \n{}'.format(e.output))


def main():
    update_clamav_definitions()

    subprocess.Popen(['clamd'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    cd = clamd.ClamdUnixSocket()
    clamd_up = False
    clamd_max_retry_count = 12
    clamd_retry_count = 0

    while not (clamd_up):
        try:
            cd.ping()
            logger.info('Clamd is up')
            clamd_up = True
        except:
            if clamd_retry_count == 12:
                raise Exception(
                    'Clamd failed to respond within {} retries'.format(clamd_max_retry_count))
            logger.warning('Clamd is not up yet, retrying in 10 seconds')
            time.sleep(10)
            clamd_retry_count += 1

    scan_target_path = '/tmp/{}'.format(file_name)
    s3object.download_file(scan_target_path)
    logger.info('Starting scan of {} in {}'.format(object_key, s3_bucket))
    scan_output = cd.scan(scan_target_path)
    scan_result = scan_output[scan_target_path][0]

    if scan_result == 'FOUND':
        infection_name = scan_output[scan_target_path][1]
        logger.info('{} is infected with {}'.format(
            object_key, infection_name))
        tag_object(s3_bucket, object_key,
                   'Infected: {}'.format(infection_name))
        delete_object(s3_bucket, object_key)
    else:
        logger.info('{} is clean'.format(object_key))
        tag_object(s3_bucket, object_key, 'Clean')


if __name__ == '__main__':
    main()