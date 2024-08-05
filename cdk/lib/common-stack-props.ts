import {EnvStackProps} from "./env-stack-props";
import {EnvProps} from "./env-props";

export interface CommonStackProps extends EnvStackProps {
  envProps: EnvProps;
  fqdn: string;
  secondaryFqdn: string;
  domainName: string;
  secondaryDomainName: string;
}
