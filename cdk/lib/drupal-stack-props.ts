import { EcsStackProps, EcsStackPropsTaskDef } from './ecs-stack-props';

export interface DrupalStackProps extends EcsStackProps {
  drupalTaskDef: EcsStackPropsTaskDef;
  sentryTracesSampleRate: string
}
