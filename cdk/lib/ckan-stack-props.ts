import { EcsStackProps, EcsStackPropsTaskDef } from './ecs-stack-props';

export interface CkanStackProps extends EcsStackProps {
  ckanTaskDef: EcsStackPropsTaskDef,
  ckanCronTaskDef: EcsStackPropsTaskDef,
  datapusherTaskDef: EcsStackPropsTaskDef,
  solrTaskDef: EcsStackPropsTaskDef,
  fusekiTaskDef: EcsStackPropsTaskDef,
  ckanCronEnabled: boolean;
  archiverSendNotificationEmailsToMaintainers: boolean;
  archiverExemptDomainsFromBrokenLinkNotifications: string[];
  cloudstorageEnabled: boolean;
}
