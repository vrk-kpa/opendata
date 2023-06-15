import {Handler, APIGatewayEvent} from 'aws-lambda';
import {GetSecretValueCommand, SecretsManagerClient} from "@aws-sdk/client-secrets-manager";
import * as https from 'https';

const { ZULIP_API_URL, ZULIP_API_USER, ZULIP_API_KEY_SECRET, ZULIP_STREAM, ZULIP_TOPIC } = process.env;

export const sendToZulip: Handler = async (event: APIGatewayEvent) => {
  const secretsManagerClient = new SecretsManagerClient({region: "eu-west-1"});
  const command = new GetSecretValueCommand({
    SecretId: ZULIP_API_KEY_SECRET
  });
  const response = await secretsManagerClient.send(command);
  const zulipApiKey = response.SecretString;

  const options: https.RequestOptions = {
    hostname: ZULIP_API_URL,
    port: 443,
    path: '/api/v1/messages',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${Buffer.from(`${ZULIP_API_USER}:${zulipApiKey}`).toString('base64')}`,
    },
  };

  const { message } = JSON.parse(event.body || '');
  const data = {
    type: 'stream',
    to: ZULIP_STREAM,
    topic: ZULIP_TOPIC,
    content: message,
  };

  https.request(options, (res: any) => {
    console.log('Response from Zulip API:', res.statusCode);
  }).on('error', (error: any) => {
    console.error('Error sending message to Zulip:', error);
  }).end(JSON.stringify(data));

  return {
    statusCode: 200,
    body: 'Message sent to Zulip',
  };
};