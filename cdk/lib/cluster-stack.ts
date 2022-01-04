import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';

import { CommonStackProps } from './common-stack-props';

export class ClusterStack extends cdk.Stack {
  readonly vpc: ec2.IVpc;
  readonly cluster: ecs.ICluster;
  readonly namespace: sd.IPrivateDnsNamespace;

  constructor(scope: cdk.Construct, id: string, props: CommonStackProps) {
    super(scope, id, props);

    this.vpc = ec2.Vpc.fromLookup(this, 'vpc', {
      vpcId: this.node.tryGetContext('vpcId'),
    });

    this.cluster = new ecs.Cluster(this, 'cluster', {
      vpc: this.vpc,
      enableFargateCapacityProviders: true,
    });

    this.namespace = new sd.PrivateDnsNamespace(this, 'namespace', {
      name: `${props.environment}-opendata-ns`,
      vpc: this.vpc,
    });
  }
}
