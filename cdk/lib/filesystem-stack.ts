import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as efs from 'aws-cdk-lib/aws-efs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

import { EfsStackProps } from './efs-stack-props';

export class FileSystemStack extends Stack {
  readonly drupalFs: efs.FileSystem;
  readonly ckanFs: efs.FileSystem;
  readonly solrFs: efs.FileSystem;
  readonly migrationFsSg?: ec2.ISecurityGroup;
  readonly migrationFs?: efs.IFileSystem;

  constructor(scope: Construct, id: string, props: EfsStackProps) {
    super(scope, id, props);

    this.drupalFs = new efs.FileSystem(this, 'drupalFs', {
      vpc: props.vpc,
      performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
      throughputMode: efs.ThroughputMode.BURSTING,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      },
      encrypted: true,
    });

    this.ckanFs = new efs.FileSystem(this, 'ckanFs', {
      vpc: props.vpc,
      performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
      throughputMode: efs.ThroughputMode.BURSTING,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      },
      encrypted: true,
    });

    this.solrFs = new efs.FileSystem(this, 'solrFs', {
      vpc: props.vpc,
      performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
      throughputMode: efs.ThroughputMode.BURSTING,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_NAT,
      },
      encrypted: true,
    });

    if (props.importMigrationFs) {
      // get params
      const pMigrationFsSgId = ssm.StringParameter.fromStringParameterAttributes(this, 'pMigrationFsSgId', {
        parameterName: `/${props.environment}/opendata/cdk/migration_fs_sg_id`,
      });
      const pMigrationFsId = ssm.StringParameter.fromStringParameterAttributes(this, 'pMigrationFsId', {
        parameterName: `/${props.environment}/opendata/cdk/migration_fs_id`,
      });

      this.migrationFsSg = ec2.SecurityGroup.fromSecurityGroupId(this, 'migrationFsSg', pMigrationFsSgId.stringValue, {
        allowAllOutbound: true,
        mutable: true,
      });

      this.migrationFs = efs.FileSystem.fromFileSystemAttributes(this, 'migrationFs', {
        fileSystemId: pMigrationFsId.stringValue,
        securityGroup: this.migrationFsSg,
      });
    }
  }
}