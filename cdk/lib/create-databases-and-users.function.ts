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
      await client.raw("CREATE ROLE ?? LOGIN PASSWORD ?;",
        [datastoreCredentialObj.username, datastoreCredentialObj.password]);
      await client.raw("CREATE DATABASE ?? OWNER ?? ENCODING 'utf-8';",
        ['datastore_jobs', datastoreCredentialObj.username])
      await client.raw("GRANT ALL PRIVILEGES ON DATABASE ?? TO ?",
        ['datastore_jobs', datastoreCredentialObj.username])

      return {
        statusCode: 200,
        body: "Db and users created"
      }
    } catch (err) {
      console.log(err)
      return {
        statusCode: 400,
        body: "something went wrog"
      }
    }

  }

}
