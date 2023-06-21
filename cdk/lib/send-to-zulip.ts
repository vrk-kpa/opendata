import {Construct} from "constructs";
import {NodejsFunction} from "aws-cdk-lib/aws-lambda-nodejs";
import {SendToZulipProps} from "./send-to-zulip-props";
import * as sm from 'aws-cdk-lib/aws-secretsmanager';

export class SendToZulip extends Construct {
  readonly lambda: NodejsFunction;
  constructor(scope: Construct, id: string, props: SendToZulipProps) {
    super(scope, id);

    // Task restart zulip reporting
    const zulipSecret = new sm.Secret(this, `/${props.environment}/opendata/common/zulip_api_key`);
    this.lambda = new NodejsFunction(this, 'function', {
      environment: {
        ZULIP_API_USER: props.zulipApiUser,
        ZULIP_API_KEY_SECRET: zulipSecret.secretName,
        ZULIP_API_URL: props.zulipApiUrl,
        ZULIP_STREAM: props.zulipStream,
        ZULIP_TOPIC: props.zulipTopic
      }
    });
    zulipSecret.grantRead(this.lambda);
  }
}
