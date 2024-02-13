import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ec from 'aws-cdk-lib/aws-elasticache';
import { Construct } from 'constructs';

import { EcStackProps } from './ec-stack-props';
import * as logs from "aws-cdk-lib/aws-logs";

export class CacheStack extends Stack {
  readonly cachePort: number;
  readonly cacheSubnets: ec2.SelectedSubnets;
  readonly cacheSubnetGroup: ec.CfnSubnetGroup;
  readonly cacheSecurityGroup: ec2.ISecurityGroup;
  readonly cacheCluster: ec.CfnCacheCluster;

  constructor(scope: Construct, id: string, props: EcStackProps) {
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

    const cacheLogGroup = new logs.LogGroup(this, 'cacheLogGroup', {
      logGroupName: `/${props.environment}/elasticache/redis`,
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
      logDeliveryConfigurations: [{
        destinationDetails: {
          cloudWatchLogsDetails: {
            logGroup: cacheLogGroup.logGroupName
          }
        },
        destinationType: 'cloudwatch-logs',
        logFormat: 'text',
        logType: 'engine-log'
      }

      ]
    });
    
  }
}
