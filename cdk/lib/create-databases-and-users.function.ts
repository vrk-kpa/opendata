import { Handler } from "aws-lambda";

import {GetSecretValueCommand, SecretsManagerClient} from "@aws-sdk/client-secrets-manager";

import { knex } from 'knex';


const {
  JOBS_SECRET,
  USER_SECRET,
  READ_SECRET,
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

  const datastoreUserCommand = new GetSecretValueCommand({
    SecretId: USER_SECRET
  });

  const datastoreUserResponse = await secretsManagerClient.send(datastoreUserCommand);
  const datastoreUserCredentials = datastoreUserResponse.SecretString;

  const datastoreReadCommand = new GetSecretValueCommand({
    SecretId: READ_SECRET
  });

  const datastoreReadResponse = await secretsManagerClient.send(datastoreReadCommand);
  const datastoreReadCredentials = datastoreReadResponse.SecretString;



  if (credentials !== undefined && datastoreJobsCredentials !== undefined &&
    datastoreUserCredentials !== undefined && datastoreReadCredentials !== undefined) {

    const credObj = JSON.parse(credentials)
    const datastoreJobsCredentialObj = JSON.parse(datastoreJobsCredentials)
    const datastoreUserCredentialObj = JSON.parse(datastoreUserCredentials)
    const datastoreReadCredentialObj = JSON.parse(datastoreReadCredentials)

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
      let datastoreUser = datastoreJobsCredentialObj.username;
      let password = datastoreJobsCredentialObj.password;
      await client.raw(
        "SET LOCAL log_statement = 'none';" +
        `CREATE ROLE ${datastoreUser} LOGIN PASSWORD '${password}'; `);
      console.log("Created datastore jobs user account")
    } catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      await client.raw("GRANT :datastoreUser: TO :admin:; ", {
        datastoreUser: datastoreJobsCredentialObj.username,
        admin: credObj.username
      })
      console.log("Granted 'datastore_jobs' role to admin")
    }
    catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }


    try {
      await client.raw("CREATE DATABASE :datastoreJobsDb: OWNER :datastoreUser: ENCODING 'utf-8'; ",
        {
          datastoreJobsDb: "datapusher_jobs",
          datastoreUser: datastoreJobsCredentialObj.username
        });
      console.log("Created database datastore_jobs")
    } catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      await client.raw("GRANT ALL PRIVILEGES ON DATABASE :datastoreJobsDb: TO :datastoreUser:; ",
        {
          datastoreJobsDb: "datapusher_jobs",
          datastoreUser: datastoreJobsCredentialObj.username
        })
      console.log("Granted all priviledges to database 'datastore_jobs' to datastore jobs user")
    } catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      let datastoreUser = datastoreUserCredentialObj.username;
      let password = datastoreUserCredentialObj.password;
      await client.raw( `CREATE ROLE ${datastoreUser} LOGIN PASSWORD '${password}'; `)
      console.log("Created datastore write user account")
    }
    catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      await client.raw("GRANT :datastoreUser: TO :admin:; ", {
        datastoreUser: datastoreUserCredentialObj.username,
        admin: credObj.username
      })
      console.log("Granted 'datastore' role to admin")
    }
    catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      await client.raw("CREATE DATABASE :datastoreDb: OWNER :datastoreUser: ENCODING 'utf-8'; ",
        {
          datastoreDb: 'datastore',
          datastoreUser: datastoreUserCredentialObj.username
        })
      console.log("Created database datastore")
    } catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      await client.raw("GRANT ALL PRIVILEGES ON DATABASE :datastoreDb: TO :datastoreUser:; ",
        {
          datastoreDb: "datastore",
          datastoreUser: datastoreUserCredentialObj.username
        })
      console.log("Granted all priviledges to database 'datastore' to datastore write user")
    } catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      let datastoreReadUser = datastoreReadCredentialObj.username;
      let password = datastoreReadCredentialObj.password;
      await client.raw(`CREATE ROLE ${datastoreReadUser} LOGIN PASSWORD '${password}'; `)
      console.log("Created datastore read user account")
    } catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

    try {
      await client.raw("GRANT :datastoreReadUser: TO :admin:; ", {
        datastoreReadUser: datastoreReadCredentialObj.username,
        admin: credObj.username
      })
      console.log("Granted 'datastore_read' role to admin")
    }
    catch (err) {
      if (err && typeof err === 'object') {
        console.log(err.toString().replace(/PASSWORD\s(.*;)/, "***"))
      }
    }

  }

  return {
    statusCode: 200,
    body: "Db and users created"

  }
}
