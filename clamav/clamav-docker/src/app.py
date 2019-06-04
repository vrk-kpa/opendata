from clams3scan import ClamS3Scanner
import logging
import os
import sys

logging.basicConfig(format='%(name)-12s: %(levelname)-8s %(message)s',
                    level=logging.INFO, stream=sys.stdout)

logger = logging.getLogger(__name__)

def main():
    s3_bucket = os.getenv('BUCKET_NAME')
    object_key = os.getenv('OBJECT_KEY')
    sns_topic_arn = os.getenv('SNS_TOPIC_ARN')

    clamscanner = ClamS3Scanner(s3_bucket, object_key, sns_topic_arn)
    scan_output = clamscanner.scan_file()
    scan_result = scan_output[next(iter(scan_output))][0]

    if scan_result == 'FOUND':
        infection_name = scan_output[next(iter(scan_output))][1]
        logger.info(f'{object_key} is infected with {infection_name}')
        tag_value = f'Infected: {infection_name}'
        clamscanner.tag_object(tag_value)
        clamscanner.delete_object()
        clamscanner.sns_publish(infection_name)
    else:
        logger.info(f'{object_key} is clean')
        clamscanner.tag_object('Clean')


if __name__ == '__main__':
    main()