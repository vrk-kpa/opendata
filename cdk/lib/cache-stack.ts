import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';
import * as efs from '@aws-cdk/aws-efs';
import * as ssm from '@aws-cdk/aws-ssm';
import * as sm from '@aws-cdk/aws-secretsmanager';
import * as ec from '@aws-cdk/aws-elasticache';

import { EcStackProps } from './ec-stack-props';

export class CacheStack extends cdk.Stack {
  readonly cachePort: number;
  readonly cacheSubnets: ec2.SelectedSubnets;
  readonly cacheSubnetGroup: ec.CfnSubnetGroup;
  readonly cacheSecurityGroup: ec2.ISecurityGroup;
  readonly cacheCluster: ec.CfnCacheCluster;

  constructor(scope: cdk.Construct, id: string, props: EcStackProps) {
    super(scope, id, props);

    this.cachePort = 6379;

    this.cacheSubnets = props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
    });

    this.cacheSubnetGroup = new ec.CfnSubnetGroup(this, 'cacheSubnetGroup', {
      description: 'cache subnet group with private NAT subnets',
      subnetIds: this.cacheSubnets.subnetIds,
    });

    this.cacheSecurityGroup = new ec2.SecurityGroup(this, 'cacheSecurityGroup', {
      vpc: props.vpc,
      allowAllOutbound: true,
      description: 'cache security group',
    });

    this.cacheCluster = new ec.CfnCacheCluster(this, 'cacheCluster', {
      cacheNodeType: props.cacheNodeType,
      engine: 'redis',
      engineVersion: props.cacheEngineVersion,
      numCacheNodes: props.cacheNumNodes,
      cacheSubnetGroupName: this.cacheSubnetGroup.ref,
      port: this.cachePort,
      preferredMaintenanceWindow: 'sun:23:00-mon:01:30',
      vpcSecurityGroupIds: [this.cacheSecurityGroup.securityGroupId],
      clusterName: `${props.environment}-opendata-cache`,
    });
    
  }
}