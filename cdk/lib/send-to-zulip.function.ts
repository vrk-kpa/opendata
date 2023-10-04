import {Handler} from 'aws-lambda';
import {GetSecretValueCommand, SecretsManagerClient} from "@aws-sdk/client-secrets-manager";
import * as https from 'https';
import FormData = require('form-data');

const { ZULIP_API_URL, ZULIP_API_USER, ZULIP_API_KEY_SECRET, ZULIP_STREAM, ZULIP_TOPIC } = process.env;

export const handler: Handler = async (event: any) => {
  if(!ZULIP_API_URL || !ZULIP_API_USER || !ZULIP_API_KEY_SECRET ||
     !ZULIP_STREAM || !ZULIP_TOPIC) {
    return {
      statusCode: 500,
      body: 'Missing configuration values',
    }
  }

  const secretsManagerClient = new SecretsManagerClient({region: "eu-west-1"});
  const command = new GetSecretValueCommand({
    SecretId: ZULIP_API_KEY_SECRET
  });
  const response = await secretsManagerClient.send(command);
  const zulipApiKey = response.SecretString;

  const { resources, detail } = event;
  const message = `${detail?.eventName}: ${resources?.join(', ')}`;
  
  const data = new FormData();
  data.append('type', 'stream');
  data.append('to', ZULIP_STREAM);
  data.append('topic', ZULIP_TOPIC);
  data.append('content', message);

  const options: https.RequestOptions = {
    hostname: ZULIP_API_URL,
    port: 443,
    path: '/api/v1/messages',
    method: 'POST',
    auth: `${ZULIP_API_USER}:${zulipApiKey}`,
    headers: data.getHeaders(),
  };

  await new Promise((resolve, reject) => {
    const req = https.request(options, (res: any) => {
      console.log('Response from Zulip API:', res.statusCode);
      if(res.statusCode != 200) {
        res.on('data', (chunk: any) => {
          console.log(chunk.toString());
        }).on('end', () => {
          resolve(res);
        });
      } else {
        resolve(res);
      }
    }).on('error', (error: any) => {
      console.error('Error sending message to Zulip:', error);
      reject(error);
    });
    data.pipe(req);
    req.end();
  });

  return {
    statusCode: 200,
    body: 'Message sent to Zulip',
  };
};