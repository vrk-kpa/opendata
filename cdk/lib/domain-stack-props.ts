import {StackProps} from "aws-cdk-lib";

export interface DomainStackProps extends StackProps{
  crossAccountId?: string,
  zoneName: string
}
