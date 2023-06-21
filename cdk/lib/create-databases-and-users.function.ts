import { Handler } from "aws-lambda";

import {GetSecretValueCommand, SecretsManagerClient} from "@aws-sdk/client-secrets-manager";

import { knex } from 'knex';


const { SECRET_NAME,
  ADMIN_SECRET } = process.env
export const handler: Handler = async (event, context) => {

  const secretsManagerClient = new SecretsManagerClient({region: "eu-west-1"})
  const command = new GetSecretValueCommand({
    SecretId: ADMIN_SECRET
  })
  const response = await secretsManagerClient.send(command);

  const credentials = response.SecretString

  const datastoreCommand = new GetSecretValueCommand({
    SecretId: SECRET_NAME
  })

  const datastoreResponse = await secretsManagerClient.send(datastoreCommand);
  const datastoreCredentials = datastoreResponse.SecretString

  if (credentials !== undefined && datastoreCredentials !== undefined) {

    const credObj = JSON.parse(credentials)
    const datastoreCredentialObj = JSON.parse(datastoreCredentials)


    const client = knex({
      client: 'pg',
      connection: {
        user: credObj.username,
        password: credObj.password,
        host: credObj.host,
        port: credObj.port,
        database: "postgres"
      }
    })

    try {
      await client.raw(
        "SET LOCAL log_statement = 'none';" +
        "CREATE ROLE :datastoreUser: LOGIN PASSWORD ':password:'; " +
        "GRANT :datastoreUser: TO :admin:; ",
        {
          datastoreUser: datastoreCredentialObj.username,
          password: datastoreCredentialObj.password,
          admin: credObj.username
        });

      await client.raw("CREATE DATABASE :datastoreDb: OWNER :datastoreUser: ENCODING 'utf-8'; ",
        {
          datastoreDb: "datastore_jobs",
          datastoreUser: datastoreCredentialObj.username
      });

      await client.raw("GRANT ALL PRIVILEGES ON DATABASE :datastoreDb: TO :datastoreUser:; ",
        {
          datastoreDb: "datastore_jobs",
          datastoreUser: datastoreCredentialObj.username
        })
    } catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
      return {
        statusCode: 400,
        body: "something went wrong"
      }
    }
  }
  return {
    statusCode: 200,
    body: "Db and users created"
  }

}
