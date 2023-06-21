import {CreateDatabasesAndUsers} from "./create-databases-and-users";
import {Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {LambdaStackProps} from "./lambda-stack-props";
import { SendToZulip } from "./send-to-zulip";
import { NodejsFunction } from "aws-cdk-lib/aws-lambda-nodejs";

export class LambdaStack extends Stack {
  readonly sendToZulipLambda: NodejsFunction;
  constructor(scope: Construct, id: string, props: LambdaStackProps ) {
    super(scope, id, props);
    new CreateDatabasesAndUsers(this, 'create-databases-and-users', {
      datastoreInstance: props.datastoreInstance,
      datastoreCredentials: props.datastoreCredentials,
      vpc: props.vpc,
      envProps: props.envProps,
      env: props.env,
      environment: props.environment,
      fqdn: props.fqdn,
      secondaryFqdn: props.secondaryFqdn,
      domainName: props.domainName,
      secondaryDomainName: props.secondaryDomainName,
    })

    const sendToZulip = new SendToZulip(this, 'send-to-zulip', {
      zulipApiUser: 'avoindata-bot@turina.dvv.fi',
      zulipApiUrl: 'https://turina.dvv.fi',
      zulipStream: 'avoindata.fi',
      zulipTopic: 'Container restarts',
      envProps: props.envProps,
      env: props.env,
      environment: props.environment,
      fqdn: props.fqdn,
      secondaryFqdn: props.secondaryFqdn,
      domainName: props.domainName,
      secondaryDomainName: props.secondaryDomainName,
    });
    this.sendToZulipLambda = sendToZulip.lambda;
  }
}
