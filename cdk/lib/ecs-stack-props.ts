import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecs from '@aws-cdk/aws-ecs';
import * as sd from '@aws-cdk/aws-servicediscovery';
import * as efs from '@aws-cdk/aws-efs';
import * as ecr from '@aws-cdk/aws-ecr';
import * as rds from '@aws-cdk/aws-rds';
import * as ec from '@aws-cdk/aws-elasticache';

import { CommonStackProps } from './common-stack-props';

export interface EcsStackProps extends CommonStackProps {
  repositories: { [key: string]: ecr.IRepository };
  vpc: ec2.IVpc;
  cluster: ecs.ICluster;
  namespace: sd.IPrivateDnsNamespace;
  fileSystems: { [key: string]: efs.FileSystem };
  migrationFileSystemProps?: MigrationFsProps;
  databaseSecurityGroup: ec2.ISecurityGroup,
  databaseInstance: rds.IDatabaseInstance,
  cachePort: number,
  cacheSecurityGroup: ec2.ISecurityGroup,
  cacheCluster: ec.CfnCacheCluster;
  drupalService?: ecs.FargateService;
  ckanService?: ecs.FargateService;
  captchaEnabled?: boolean;
  analyticsEnabled?: boolean;
}

export interface MigrationFsProps {
  securityGroup: ec2.ISecurityGroup;
  fileSystem: efs.IFileSystem;
}

export interface EcsStackPropsTaskDef {
  /**
   * The number of cpu units used by the task.
   * 256 (0.25 vCPU), 512 (0.5 vCPU), 1024 (1.0 vCPU), 2048 (2.0 vCPU), 4096 (4.0 vCPU)
   */
  taskCpu: number;
  /**
   * The amount (in MiB) of memory used by the task.
   * 0.25 vCPU: 512MB, 1024MB, 2048MB
   * 0.5  vCPU: 1024MB, 2048MB, 3072MB, 4096MB
   * 1.0  vCPU: 2048MB, 3072MB, 4096MB, 5120MB, 6144MB, 7168MB, 8192MB
   * 2.0  vCPU: 4096MB, 16384MB in increments of 1024MB
   * 4.0  vCPU: 8192MB, 30720MB in increments of 1024MB
   */
  taskMem: number;
}
