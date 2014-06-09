#!/usr/bin/env python

import boto.exception
import boto.cloudformation
import boto.sns
import requests
import time
import os
import shutil
import subprocess
import json
import logging
import base64

import settings
import secrets

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class ContinuousDeployer:
    """Wrapper around Ansible, Git and AWS CloudFormation for automated deployments."""

    ec2 = None
    cloudform = None
    deploy_id = ""
    deploy_path = ""
    commit_details = None
    cloudform_outputs = {}

    def __init__(self, project_prefix):
        self.deploy_id = "cd-" + project_prefix + "-" + str(int(time.time() * 1000))
        self.deploy_path = settings.relative_cache_path + self.deploy_id
        log.debug("Deployment ID: " + self.deploy_id)
        try:
            os.makedirs(self.deploy_path)
        except OSError:
            log.error("Failed to create cache directory for deployment")
            raise

        file_logger = logging.FileHandler(self.deploy_path + '/deploy.log')
        file_logger.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        file_logger.setFormatter(file_formatter)
        log.addHandler(file_logger)

        self.sns = boto.sns.connect_to_region(settings.region,
                                              aws_access_key_id=secrets.aws_access_key_id,
                                              aws_secret_access_key=secrets.aws_secret_access_key)
        self.cloudform = boto.cloudformation.connect_to_region(settings.region,
                                                               aws_access_key_id=secrets.aws_access_key_id,
                                                               aws_secret_access_key=secrets.aws_secret_access_key)

    def prepare_sources(self):
        """Clone and extract sources and store last commit information."""

        with open(os.devnull, "w") as devnull:
            log.info("Fetching sources from git")
            subprocess.call(["git", "clone", settings.git_url_ytp], cwd=self.deploy_path, stdout=devnull, stderr=devnull)

            try:
                git_log_format = "--pretty=format:{\"CommitId\":\"%H\",\"CommitDetails\":\"%an %f %ad\"}"
                self.commit_details = json.loads(subprocess.check_output(["git", "log", "-1", git_log_format], cwd=self.deploy_path+"/ytp"))
            except:
                log.error("Failed to get commit details")
                raise

            try:
                subprocess.call(["ssh-agent bash -c 'ssh-add " + secrets.git_keyfile + "; cd " +
                                self.deploy_path + "/ytp/ansible/vars; git clone " + settings.git_url_secrets + "'"],
                                shell=True, stdout=devnull, stderr=devnull)

                process_extract = subprocess.Popen(["./secret.sh", "decrypt"],
                                                   cwd=self.deploy_path+"/ytp/ansible/vars/ytp-secrets",
                                                   stdin=subprocess.PIPE, stdout=devnull, stderr=devnull)
                process_extract.communicate(secrets.passphrase + "\n")
            except:
                log.error("Failed to clone and decrypt ytp-secrets")
                raise                

    def create_infrastructure_stack(self, template_filename):
        """Create an infrastructure stack based on a cloudformation template."""

        log.info("Creating infrastructure based on template " + template_filename)
        with open(settings.relative_template_path + template_filename, "r") as template_file:
            template = template_file.read()

        stack_parameters = [("KeyName", secrets.aws_instance_key_name), ("DeploymentId", self.deploy_id)]

        self.cloudform.create_stack(self.deploy_id, template_body=template, parameters=stack_parameters, tags=self.commit_details, timeout_in_minutes=10)
        log.debug("Successfully requested for stack")

    def wait_for_stack_creation(self):
        """Wait for cloudformation to create the stack. Crude waiting done by polling, could be replaced with SNS."""

        log.debug("Waiting for stack to come up")
        started_waiting = time.time()
        while time.time()-started_waiting < settings.cloudformation_create_timeout:
            try:
                events = self.cloudform.describe_stack_events(stack_name_or_id=self.deploy_id)

                if (len(events) > 0 and
                   events[0].resource_type == "AWS::CloudFormation::Stack" and
                   events[0].logical_resource_id == self.deploy_id and
                   events[0].resource_status == "CREATE_COMPLETE"):
                    log.debug("Stack is now ready (took {0} seconds)".format(int(time.time()-started_waiting)))
                    return
            except boto.exception.BotoServerError:
                log.warning("Server error, maybe stack does not exist yet")
            time.sleep(settings.cloudformation_create_pollrate)
        return

    def generate_inventory_file(self):
        """Generate a static inventory file from cloudformation outputs."""

        try:
            log.debug("Fetching cloudformation outputs")
            outputs = self.cloudform.describe_stacks(stack_name_or_id=self.deploy_id)[0].outputs
            for output in outputs:
                self.cloudform_outputs[output.key] = output.value

            log.info("Generating inventory file")
            with open(self.deploy_path + "/ytp/ansible/auto-generated-inventory", "w") as inventory:
                inventory.write("[webserver]\n" + self.cloudform_outputs['PublicDNSWeb'] +
                                "\n\n[webserver:vars]\nsecret_variables=variables-alpha.yml\n\n" +
                                "[dbserver]\n" + self.cloudform_outputs['PublicDNSDb'] +
                                "\n\n[dbserver:vars]\nsecret_variables=variables-alpha.yml\n\n")
        except:
            log.error("Failed to generate inventory")
            raise

    def run_playbook(self, playbookfile):
        """Run a playbook."""

        log.info("Running playbook " + playbookfile)
        start_time = time.time()
        try:
            with open(self.deploy_path+"/"+playbookfile+"-"+str(time.time())+"-std.log", "w") as logfile_std:
                with open(self.deploy_path+"/"+playbookfile+"-"+str(time.time())+"-err.log", "w") as logfile_err:
                    return_code = subprocess.call(["ansible-playbook --private-key=" + secrets.aws_keyfile + " -i auto-generated-inventory --user=ubuntu " +
                                                  playbookfile], shell=True, cwd=self.deploy_path+"/ytp/ansible", stdout=logfile_std, stderr=logfile_err)
                    if return_code != 0:
                        raise Exception("Running the playbook returned code", return_code)
                    log.debug("Finished running playbook {0} in {1} seconds".format(playbookfile, int(time.time()-start_time)))
        except:
            log.error("Failed running playbook {0} after {1} seconds".format(playbookfile, int(time.time()-start_time)))
            log.error("Ansible logs:\n" + subprocess.check_output(["tail -n 15 " + playbookfile + "*.log"], shell=True, cwd=self.deploy_path))

    def test_http(self, url):
        """Simple checks to see if deployment succeeded."""

        req = requests.get(url, verify=False)
        log.debug("Server returned ok for " + url) if req.status_code == 200 else log.error("Server returned {0} for {1}".format(req.status_code, url))

    def send_report(self):
        """Send deployment report as SNS, which can be subscribed with email etc from AWS console."""

        log.debug("Preparing report")
        title = "[{0}] Deploy {1}".format(settings.project_prefix, self.deploy_id)
        message = "Deployment report {0} - {1}\n\n".format(self.deploy_id, time.strftime("%c"))

        try:
            title = "[{0}] Deploy ({1})".format(settings.project_prefix, self.commit_details["CommitDetails"])
            message += subprocess.check_output(["tail -n 50 deploy.log"], shell=True, cwd=self.deploy_path)
        except:
            log.error("Failed to buildup report")
        self.sns.publish(topic=secrets.aws_arn, message=message, subject=title)

    def cleanup(self):
        """Delete stack and clean up all local files created for this deployment."""

        try:
            self.cloudform.delete_stack(self.deploy_id)
        except:
            log.warning("Failed to delete stack, something might be left running in AWS!")
        log.debug("Removing source files")
        shutil.rmtree(self.deploy_path + "/ytp")


if __name__ == "__main__":

    deploy = ContinuousDeployer(settings.project_prefix)

    try:
        deploy.prepare_sources()
        deploy.create_infrastructure_stack(settings.cloudformation_templatefile)
        deploy.wait_for_stack_creation()
        deploy.generate_inventory_file()

        deploy.run_playbook("connection-test.yml")
        deploy.run_playbook("cluster-dbserver.yml")
        deploy.run_playbook("cluster-webserver.yml")

        deploy.test_http('http://' + deploy.cloudform_outputs['PublicDNSWeb'] + '/')
        deploy.test_http('https://' + deploy.cloudform_outputs['PublicDNSWeb'] + '/data/fi/dataset')

        log.info("Running playbooks again to test incremental configuration")
        deploy.run_playbook("cluster-dbserver.yml")
        deploy.run_playbook("cluster-webserver.yml")

        deploy.test_http('http://' + deploy.cloudform_outputs['PublicDNSWeb'] + '/')
        deploy.test_http('https://' + deploy.cloudform_outputs['PublicDNSWeb'] + '/data/fi/dataset')

        deploy.send_report()
        deploy.cleanup()

    except Exception, e:
        import traceback
        deploy.sns.publish(topic=secrets.aws_arn, message=base64.b64encode(traceback.format_exc()), subject="Auto-deployment script failed")
