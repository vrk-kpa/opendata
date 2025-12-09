import {EnvStackProps} from "./env-stack-props";
import {EnvProps} from "./env-props";

export interface CommonStackProps extends EnvStackProps {
  envProps: EnvProps;
  webFqdn: string;
}
