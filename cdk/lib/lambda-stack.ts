import {CreateDatabasesAndUsers} from "./create-databases-and-users";
import {Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {LambdaStackProps} from "./lambda-stack-props";
import { SendToZulip } from "./send-to-zulip";
import {Credentials} from "aws-cdk-lib/aws-rds";
import { Topic } from "aws-cdk-lib/aws-sns";
import { LambdaSubscription } from 'aws-cdk-lib/aws-sns-subscriptions';

export class LambdaStack extends Stack {
  readonly sendToZulipTopic: Topic;
  readonly datastoreJobsCredentials: Credentials;
  readonly datastoreReadCredentials: Credentials;
  readonly datastoreUserCredentials: Credentials;
  constructor(scope: Construct, id: string, props: LambdaStackProps ) {
    super(scope, id, props);
    const createDatabases = new CreateDatabasesAndUsers(this, 'create-databases-and-users', {
      datastoreInstance: props.datastoreInstance,
      datastoreCredentials: props.datastoreCredentials,
      vpc: props.vpc,
      env: props.env,
      environment: props.environment,

    })

    this.datastoreJobsCredentials = Credentials.fromSecret(createDatabases.datastoreJobsSecret);
    this.datastoreReadCredentials = Credentials.fromSecret(createDatabases.datastoreReadSecret);
    this.datastoreUserCredentials = Credentials.fromSecret(createDatabases.datastoreUserSecret);

    const sendToZulip = new SendToZulip(this, 'send-to-zulip', {
      zulipApiUser: 'avoindata-bot@turina.dvv.fi',
      zulipApiUrl: 'turina.dvv.fi',
      zulipStream: 'Avoindata.fi',
      zulipTopic: 'Service events',
      env: props.env,
      environment: props.environment,
    });

    this.sendToZulipTopic = new Topic(this, 'monitoringTopic');
    this.sendToZulipTopic.addSubscription(new LambdaSubscription(sendToZulip.lambda));
  }
}
