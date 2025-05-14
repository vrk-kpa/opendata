import {StackProps} from "aws-cdk-lib";

export interface DomainStackProps extends StackProps{
  fqdn: string,
  secondaryFqdn: string,
  tertiaryFqdn?: string,
  crossAccountId?: string,
  zoneName: string
}
