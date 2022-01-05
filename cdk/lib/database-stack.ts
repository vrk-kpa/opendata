import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as cdk from 'aws-cdk-lib/core';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as rds from 'aws-cdk-lib/aws-rds';
import { Construct } from 'constructs';

import { RdsStackProps } from './rds-stack-props';

export class DatabaseStack extends Stack {
  readonly databaseSecurityGroup: ec2.ISecurityGroup;
  readonly databaseInstance: rds.IDatabaseInstance;

  constructor(scope: Construct, id: string, props: RdsStackProps) {
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