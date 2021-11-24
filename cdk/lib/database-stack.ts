import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';
import * as efs from '@aws-cdk/aws-efs';
import * as ssm from '@aws-cdk/aws-ssm';
import * as sm from '@aws-cdk/aws-secretsmanager';
import * as rds from '@aws-cdk/aws-rds';

import { RdsStackProps } from './rds-stack-props';

export class DatabaseStack extends cdk.Stack {
  readonly databaseSecurityGroup: ec2.ISecurityGroup;
  readonly databaseInstance: rds.IDatabaseInstance;

  constructor(scope: cdk.Construct, id: string, props: RdsStackProps) {
    super(scope, id, props);

    // get params
    const pDbSgId = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbSg', {
      parameterName: `/${props.environment}/opendata/cdk/db_sg_id`,
    });
    const pDbHost = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbHost', {
      parameterName: `/${props.environment}/opendata/common/db_host`,
    });

    this.databaseSecurityGroup = ec2.SecurityGroup.fromSecurityGroupId(this, 'databaseSecurityGroup', pDbSgId.stringValue, {
      allowAllOutbound: true,
      mutable: true,
    });

    this.databaseInstance = rds.DatabaseInstance.fromDatabaseInstanceAttributes(this, 'databaseInstance', {
      instanceEndpointAddress: pDbHost.stringValue,
      instanceIdentifier: pDbHost.stringValue.split('.')[0],
      port: 5432,
      securityGroups: [this.databaseSecurityGroup],
    });
    
  }
}