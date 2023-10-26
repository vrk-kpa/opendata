import { EcsStackProps, EcsStackPropsTaskDef } from './ecs-stack-props';
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as rds from "aws-cdk-lib/aws-rds";
import {ISecret} from "aws-cdk-lib/aws-secretsmanager";
import { CkanUwsgiProps } from './ckan-uwsgi-props';

export interface CkanStackProps extends EcsStackProps {
  ckanTaskDef: EcsStackPropsTaskDef,
  ckanCronTaskDef: EcsStackPropsTaskDef,
  datapusherTaskDef: EcsStackPropsTaskDef,
  solrTaskDef: EcsStackPropsTaskDef,
  fusekiTaskDef: EcsStackPropsTaskDef,
  ckanUwsgiProps: CkanUwsgiProps,
  ckanCronEnabled: boolean;
  archiverSendNotificationEmailsToMaintainers: boolean;
  archiverExemptDomainsFromBrokenLinkNotifications: string[];
  cloudstorageEnabled: boolean;
  datastoreSecurityGroup: ec2.ISecurityGroup,
  datastoreInstance: rds.IDatabaseInstance,
  datastoreCredentials: rds.Credentials,
  datastoreJobsCredentials: rds.Credentials,
  datastoreUserCredentials: rds.Credentials,
  datastoreReadCredentials: rds.Credentials
}
