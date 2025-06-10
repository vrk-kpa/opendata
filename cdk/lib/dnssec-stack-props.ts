import {StackProps} from "aws-cdk-lib";
import { IHostedZone } from "aws-cdk-lib/aws-route53";
export interface DnssecStackProps extends StackProps {
  zones: IHostedZone[];
}
