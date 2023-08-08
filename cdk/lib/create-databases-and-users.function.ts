import { Handler } from "aws-lambda";

import {GetSecretValueCommand, SecretsManagerClient} from "@aws-sdk/client-secrets-manager";

import { knex } from 'knex';


const { JOBS_SECRET,
  ADMIN_SECRET } = process.env
export const handler: Handler = async (event, context) => {

  const secretsManagerClient = new SecretsManagerClient({region: "eu-west-1"})
  const command = new GetSecretValueCommand({
    SecretId: ADMIN_SECRET
  })
  const response = await secretsManagerClient.send(command);

  const credentials = response.SecretString

  const datastoreCommand = new GetSecretValueCommand({
    SecretId: JOBS_SECRET
  })

  const datastoreResponse = await secretsManagerClient.send(datastoreCommand);
  const datastoreJobsCredentials = datastoreResponse.SecretString

  if (credentials !== undefined && datastoreJobsCredentials !== undefined) {

    const credObj = JSON.parse(credentials)
    const datastoreJobsCredentialObj = JSON.parse(datastoreJobsCredentials)


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
          datastoreUser: datastoreJobsCredentialObj.username,
          password: datastoreJobsCredentialObj.password,
          admin: credObj.username
        });

      await client.raw("CREATE DATABASE :datastoreJobsDb: OWNER :datastoreUser: ENCODING 'utf-8'; ",
        {
          datastoreJobsDb: "datastore_jobs",
          datastoreUser: datastoreJobsCredentialObj.username
      });

      await client.raw("GRANT ALL PRIVILEGES ON DATABASE :datastoreJobsDb: TO :datastoreUser:; ",
        {
          datastoreJobsDb: "datastore_jobs",
          datastoreUser: datastoreJobsCredentialObj.username
        })

      await client.raw("CREATE DATABASE :datastoreDb: OWNER :datastoreAdmin: ENCODING 'utf-8'; ",
        {
          datastoreDb: 'datastore',
          datastoreAdmin: credObj.username
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
