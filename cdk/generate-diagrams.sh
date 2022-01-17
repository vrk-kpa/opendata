#!/bin/sh

# main application stacks
cfn-dia d -c -t cdk.out/ClusterStack-infratest.template.json -o cluster-stack.drawio
cfn-dia d -c -t cdk.out/CkanStack-infratest.template.json -o ckan-stack.drawio -e \
  AWS::EC2::SecurityGroupIngress \
  AWS::IAM::Policy \
  AWS::CDK::Metadata
cfn-dia d -c -t cdk.out/DrupalStack-infratest.template.json -o drupal-stack.drawio -e \
  AWS::EC2::SecurityGroupIngress \
  AWS::IAM::Policy \
  AWS::CDK::Metadata
cfn-dia d -c -t cdk.out/WebStack-infratest.template.json -o web-stack.drawio -e \
  AWS::EC2::SecurityGroupIngress \
  AWS::IAM::Policy \
  AWS::CDK::Metadata

# surrounding infrastructure stacks
cfn-dia d -c -t cdk.out/CacheStack-infratest.template.json -o cache-stack.drawio -e \
  AWS::CDK::Metadata
cfn-dia d -c -t cdk.out/DatabaseStack-infratest.template.json -o database-stack.drawio -e \
  AWS::CDK::Metadata
cfn-dia d -c -t cdk.out/FileSystemStack-infratest.template.json -o filesystem-stack.drawio -e \
  AWS::CDK::Metadata
cfn-dia d -c -t cdk.out/LoadBalancerStackInfratest-infratest.template.json -o loadbalancer-stack.drawio -e \
  AWS::CDK::Metadata
