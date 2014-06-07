#!/usr/bin/env python

import boto.ec2
import boto.exception
import boto.cloudformation
import pprint
import time
import os
import shutil
import subprocess
import json

import settings
import secrets


class ContinuousDeployer:

    ec2 = None
    cloudform = None
    deploy_id = ""
    deploy_path = ""
    commit_details = None

    # Constructor
    def __init__(self, project_prefix):
        self.deploy_id = "cd-" + project_prefix + "-" + str(int(time.time() * 1000))
        self.deploy_path = settings.relative_cache_path + self.deploy_id
        self.ec2 = boto.ec2.connect_to_region(settings.region,
                                              aws_access_key_id=secrets.aws_access_key_id,
                                              aws_secret_access_key=secrets.aws_secret_access_key)
        self.cloudform = boto.cloudformation.connect_to_region(settings.region,
                                                               aws_access_key_id=secrets.aws_access_key_id,
                                                               aws_secret_access_key=secrets.aws_secret_access_key)

        try:
            os.makedirs(self.deploy_path)
        except OSError:
            print "Failed to create cache directory for deployment"
            raise

    # Clone and extract sources and store last commit information
    def prepare_sources(self):
        with open(os.devnull, "w") as devnull:
            subprocess.call(["git", "clone", settings.git_url_ytp], cwd=self.deploy_path, stdout=devnull, stderr=devnull)

            try:
                git_log_format = "--pretty=format:{\"CommitId\":\"%H\",\"CommitDetails\":\"%an %ad %f\"}"
                self.commit_details = json.loads(subprocess.check_output(["git", "log", "-1", git_log_format], cwd=self.deploy_path+"/ytp"))
            except:
                print "Failed to get commit details"
                raise

            subprocess.call(["ssh-agent bash -c 'ssh-add " + settings.keyfilename + "; cd " +
                            self.deploy_path + "/ytp/ansible/vars; git clone " + settings.git_url_secrets + "'"],
                            shell=True, stdout=devnull, stderr=devnull)

            process_extract = subprocess.Popen(["./secret.sh", "decrypt"],
                                               cwd=self.deploy_path+"/ytp/ansible/vars/ytp-secrets",
                                               stdin=subprocess.PIPE, stdout=devnull, stderr=devnull)
            process_extract.communicate(secrets.passphrase + "\n")

    # Lists instances
    def list_instances(self):
        for reservation in self.ec2.get_all_reservations():
            for instance in reservation.instances:
                pprint.pprint(instance)
                print instance.tags

    # Create an infrastructure stack based on a cloudformation template
    def create_infrastructure_stack(self, template_filename):
        with open(settings.relative_template_path + template_filename, "r") as template_file:
            template = template_file.read()

        stack_parameters = [("KeyName", secrets.aws_instance_key_name), ("DeploymentId", self.deploy_id)]

        self.cloudform.create_stack(self.deploy_id, template_body=template, parameters=stack_parameters, tags=self.commit_details, timeout_in_minutes=10)

    # Wait for cloudformation to create the stack. Crude waiting done by polling, could be replaced with SNS
    def wait_for_stack_creation(self):
        slept = 0
        while slept < settings.cloudformation_create_timeout:
            try:
                events = self.cloudform.describe_stack_events(stack_name_or_id=self.deploy_id)

                if (len(events) > 0 and
                   events[0].resource_type == "AWS::CloudFormation::Stack" and
                   events[0].logical_resource_id == self.deploy_id and
                   events[0].resource_status == "CREATE_COMPLETE"):
                    print "Stack is now ready"
                    return
            except boto.exception.BotoServerError:
                print "Server error, maybe stack does not exist yet"

            slept += settings.cloudformation_create_pollrate
            time.sleep(settings.cloudformation_create_pollrate)
        return

    # Removes all files created for this deployment
    def cleanup(self):
        print "Removing all temporary files"
        shutil.rmtree(self.deploy_path)


# Main function
if __name__ == "__main__":

    deploy = ContinuousDeployer(settings.project_prefix)

    print "Deployment id", deploy.deploy_id

    # deploy.list_instances()

    deploy.prepare_sources()

    deploy.create_infrastructure_stack(settings.cloudformation_templatefile)

    deploy.wait_for_stack_creation()

    # time.sleep(10)
    deploy.cleanup()

    # startup infrastructure, wait for infra to come up
    # deploy with ansible and dynamic inventory
    # wait for deployment
    # if deploy comes up, run basic tests
    # if ok, run incremental deployment
    # wait
    # if deploy comes up, run basic tests
    # report and cleanup
