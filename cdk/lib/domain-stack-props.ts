import {StackProps} from "aws-cdk-lib";

export interface DomainStackProps extends StackProps{
  prodAccountId?: string,
  crossAccountId?: string,
  zoneName: string
}
