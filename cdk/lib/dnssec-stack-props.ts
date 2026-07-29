import {StackProps} from "aws-cdk-lib";
import { IHostedZone } from "aws-cdk-lib/aws-route53";
import {OldDomain} from "./env-props";
export interface DnssecStackProps extends StackProps {
  oldDomains: OldDomain[];
  zone: IHostedZone;
  keyAlias: string;
}
