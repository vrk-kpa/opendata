import {Construct} from "constructs";
import {NodejsFunction} from "aws-cdk-lib/aws-lambda-nodejs";
import {SendToZulipProps} from "./send-to-zulip-props";
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import {aws_lambda} from "aws-cdk-lib";

export class SendToZulip extends Construct {
  readonly lambda: NodejsFunction;
  constructor(scope: Construct, id: string, props: SendToZulipProps) {
    super(scope, id);

    // Task restart zulip reporting
    const zulipSecret = sm.Secret.fromSecretNameV2(this, 'sZulipSecret', `/${props.environment}/zulip_api_key`);

    this.lambda = new NodejsFunction(this, 'function', {
      environment: {
        ZULIP_API_USER: props.zulipApiUser,
        ZULIP_API_KEY_SECRET: zulipSecret.secretName,
        ZULIP_API_URL: props.zulipApiUrl,
        ZULIP_STREAM: props.zulipStream,
        ZULIP_TOPIC: props.zulipTopic
      },
      runtime: aws_lambda.Runtime.NODEJS_20_X,
    });
    zulipSecret.grantRead(this.lambda);
  }
}
