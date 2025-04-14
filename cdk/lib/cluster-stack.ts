import { Stack } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as sd from 'aws-cdk-lib/aws-servicediscovery';
import { Construct } from 'constructs';

import {ClusterStackProps} from "./cluster-stack-props";

export class ClusterStack extends Stack {
  readonly vpc: ec2.IVpc;
  readonly cluster: ecs.ICluster;
  readonly namespace: sd.IPrivateDnsNamespace;

  constructor(scope: Construct, id: string, props: ClusterStackProps) {
    super(scope, id, props);

    this.vpc = ec2.Vpc.fromLookup(this, 'vpc', {
      vpcId: props.vpcId
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
