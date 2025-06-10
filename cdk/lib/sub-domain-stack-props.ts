import {StackProps} from "aws-cdk-lib";

export interface SubDomainStackProps extends StackProps {
    prodAccountId: string;
    subDomainName: string;
}
