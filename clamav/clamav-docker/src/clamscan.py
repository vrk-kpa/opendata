import clamd
import logging
import subprocess
import time

logger = logging.getLogger(__name__)


def clamd_check(decorated):
    def wrapper(*args):
        while not args[0].clamd_up:
            try:
                args[0].clamd_client.ping()
            except Exception:
                time.sleep(5)
        return decorated(*args)
    return wrapper


class ClamScanner:
    clamd_up = False
    clamd_client = clamd.ClamdUnixSocket(path="/tmp/clamd.sock")

    def __init__(self, file_name):
        self.file = file_name
        self.start_clam_daemon()
        self.update_clamav_definitions()


    @staticmethod
    def update_clamav_definitions():
        try:
            logger.info('Updating ClamAV database')
            freshclam_process_output = subprocess.check_output(
                'freshclam').decode('utf-8')
            updated = freshclam_process_output.count('updated')
            up_to_date = freshclam_process_output.count('is up-to-date')
            if updated + up_to_date < 3:
                raise Exception(
                    f'Unable to ensure that ClamAV database is up to date: \n'
                    f'{freshclam_process_output}')
            elif updated == 0:
                logger.info('ClamAV database is up to date')
            else:
                logger.info('ClamAV database updated')
        except subprocess.CalledProcessError as e:
            error_message = e.output.decode('utf-8')
            outdated = 'OUTDATED' in error_message
            components_up_to_date = error_message.count('is up to date') >= 3
            database_updated = 'ClamAV database updated' in error_message
            if outdated and components_up_to_date or database_updated:
                logger.warn('A newer version of ClamAV is available')
            else:
                logger.error(f'ClamAV database update failed: \n{e.output}')
                raise(e)

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
            except Exception:
                if clamd_retry_count == 12:
                    raise Exception(
                        f'Clamd failed to respond within {clamd_max_retry_count} retries')
                logger.warning('Clamd is not up yet, retrying in 10 seconds')
                time.sleep(10)
                clamd_retry_count += 1

    @clamd_check
    def scan_file(self):
        try:
            scan_target_path = self.file
            logger.info(
                f'Starting scan of {self.file}')
            scan_output = self.clamd_client.scan(scan_target_path)
            return scan_output

        except clamd.ClamdError as e:
            logger.error(f'Clamd scan failed: \n{e}')
            raise e
