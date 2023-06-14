import {Handler, APIGatewayEvent} from 'aws-lambda';
import {GetSecretValueCommand, SecretsManagerClient} from "@aws-sdk/client-secrets-manager";
import https from 'https';

const { ZULIP_API_URL, ZULIP_API_KEY_SECRET, ZULIP_STREAM, ZULIP_TOPIC } = process.env;

export const sendToZulip: Handler = async (event: APIGatewayEvent) => {
  const secretsManagerClient = new SecretsManagerClient({region: "eu-west-1"});
  const command = new GetSecretValueCommand({
    SecretId: ZULIP_API_KEY_SECRET
  });
  const response = await secretsManagerClient.send(command);
  const zulipApiKey = response.SecretString;

  const { message } = JSON.parse(event.body || '');

  const options: https.RequestOptions = {
    hostname: ZULIP_API_URL,
    port: 443,
    path: '/api/v1/messages',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${Buffer.from(`api:${zulipApiKey}`).toString('base64')}`,
    },
  };

  const req = https.request(options, (res) => {
    console.log('Zulip API response:', res.statusCode);

    res.on('data', (chunk) => {
      console.log('Message sent to Zulip:', chunk.toString());
    });
  });

  req.on('error', (error) => {
    console.error('Error sending message to Zulip:', error);
  });

  req.write(
    JSON.stringify({
      type: 'stream',
      to: ZULIP_STREAM,
      topic: ZULIP_TOPIC,
      content: message,
    })
  );
  req.end();

  return {
    statusCode: 200,
    body: 'Message sent to Zulip',
  };
};