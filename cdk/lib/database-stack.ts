import {aws_lambda_nodejs, Fn, Stack} from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as rds from 'aws-cdk-lib/aws-rds';
import { Construct } from 'constructs';

import { RdsStackProps } from './rds-stack-props';
import * as bak from "aws-cdk-lib/aws-backup";
import {InstanceType, Subnet} from "aws-cdk-lib/aws-ec2";
import {Credentials} from "aws-cdk-lib/aws-rds";
import {Key} from "aws-cdk-lib/aws-kms";

export class DatabaseStack extends Stack {
  readonly databaseSecurityGroup: ec2.ISecurityGroup;
  readonly datastoreSecurityGroup: ec2.ISecurityGroup;
  readonly databaseInstance: rds.IDatabaseInstance;
  readonly datastoreInstance: rds.IDatabaseInstance;
  readonly datastoreCredentials: rds.Credentials;

  constructor(scope: Construct, id: string, props: RdsStackProps) {
    super(scope, id, props);

    // get params
    const pDbSgId = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbSg', {
      parameterName: `/${props.environment}/opendata/cdk/db_sg_id`,
    });
    const pDbHost = ssm.StringParameter.fromStringParameterAttributes(this, 'pDbHost', {
      parameterName: `/${props.environment}/opendata/common/db_host`,
    });

    const pDatastoreInstanceType = ssm.StringParameter.fromStringParameterName(this, 'pDatastoreInstanceType',
      `/${props.environment}/opendata/cdk/datastore_instance_type`)

    this.databaseSecurityGroup = ec2.SecurityGroup.fromSecurityGroupId(this, 'databaseSecurityGroup', pDbSgId.stringValue, {
      allowAllOutbound: true,
      mutable: true,
    });

    this.databaseInstance = rds.DatabaseInstance.fromDatabaseInstanceAttributes(this, 'databaseInstance', {
      instanceEndpointAddress: pDbHost.stringValue,
      instanceIdentifier: `avoindata-${props.environment}`,
      port: 5432,
      securityGroups: [this.databaseSecurityGroup],
    });

    this.datastoreSecurityGroup = new ec2.SecurityGroup(this, 'datastoreSecurityGroup', {
      vpc: props.vpc
    })

    const privateSubnetA = Fn.importValue('vpc-SubnetPrivateA')
    const privateSubnetB = Fn.importValue('vpc-SubnetPrivateB')

    const encryptionKey = Key.fromLookup(this, 'EncryptionKey', {
      aliasName: `alias/secrets-key-${props.environment}`
    })

    const databaseSecret = new rds.DatabaseSecret(this,'datastoreAdminSecret', {
      username: "datastoreAdmin",
      encryptionKey: encryptionKey
    });

    this.datastoreCredentials = Credentials.fromSecret(databaseSecret);



    this.datastoreInstance = new rds.DatabaseInstance(this, 'datastoreInstance', {
      engine: rds.DatabaseInstanceEngine.postgres({version: rds.PostgresEngineVersion.VER_16}),
      allowMajorVersionUpgrade: false,
      credentials: this.datastoreCredentials,
      vpc: props.vpc,
      port: 5432,
      instanceType: new InstanceType(pDatastoreInstanceType.stringValue),
      multiAz: props.multiAz,
      allocatedStorage: 50,
      maxAllocatedStorage: 500,
      vpcSubnets: {
        subnets: [Subnet.fromSubnetId(this, 'subnetA', privateSubnetA), Subnet.fromSubnetId(this, 'subnetB', privateSubnetB)]
      },
      securityGroups: [
        this.datastoreSecurityGroup
      ]
    })

    if (props.backups && props.backupPlan ) {
      props.backupPlan.addSelection('backupPlanDatabaseSelection', {
        resources: [
          bak.BackupResource.fromRdsDatabaseInstance(this.databaseInstance)
        ]
      });
    }
  }
}
