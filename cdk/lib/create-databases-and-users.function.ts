import { Handler } from "aws-lambda";

import {GetSecretValueCommand, SecretsManagerClient} from "@aws-sdk/client-secrets-manager";
import {Client} from "pg";


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

    const pgClient = new Client({
      user: credObj.username,
      password: credObj.password,
      host: credObj.host,
      port: credObj.port,
      database: "postgres"
    })

    await pgClient.connect();

    const roleQuery = await pgClient.query(
      `DO
        $do$
        BEGIN
          IF EXISTS (
            SELECT FROM pg_catalog.pg_roles
            WHERE  rolname = $1) THEN

            RAISE NOTICE 'Role "$1" already exists. Skipping.';
          ELSE
            BEGIN   -- nested block
              CREATE ROLE $1 LOGIN PASSWORD $2;
            EXCEPTION
              WHEN duplicate_object THEN
                RAISE NOTICE 'Role "$1" was just created by a concurrent transaction. Skipping.';
            END;
          END IF;
        END
        $do$;`,
      [datastoreCredentialObj.username, datastoreCredentialObj.password]
    );


    const dbQuery = await pgClient.query(`SELECT FROM pg_database WHERE datname = $1`, [datastoreCredentialObj.username])
    if (dbQuery.rows.length === 0){
      return {
        statusCode: 200,
        body: "DB does not exist"
      }
    }
    else{
      return {
        statusCode: 200,
        body: "DB exists"
      }
    }


  }



  return {
    statusCode: 200,
    body: JSON.stringify(response)
  }

}
