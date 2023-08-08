import {Construct} from "constructs";
import {NodejsFunction} from "aws-cdk-lib/aws-lambda-nodejs";
import {aws_ec2, aws_rds} from "aws-cdk-lib";
import {CreateDatabasesAndUsersProps} from "./create-databases-and-users-props";
import {Trigger, TriggerFunction} from "aws-cdk-lib/triggers";
import {Key} from "aws-cdk-lib/aws-kms";
import {ISecret} from "aws-cdk-lib/aws-secretsmanager";


export class CreateDatabasesAndUsers extends Construct {
  readonly datastoreJobsSecret: ISecret;
  constructor(scope: Construct, id: string, props: CreateDatabasesAndUsersProps) {
    super(scope, id);

    const encryptionKey = Key.fromLookup(this, 'EncryptionKey', {
      aliasName: `alias/secrets-key-${props.environment}`
    })

    this.datastoreJobsSecret = new aws_rds.DatabaseSecret(this, "datastoreJobsSecret", {
      username: "datastore_jobs",
      encryptionKey: encryptionKey
    })

    const datastoreAdminSecret = props.datastoreCredentials.secret

    if (datastoreAdminSecret?.secretName !== undefined) {

      const secGroup = new aws_ec2.SecurityGroup(this, 'LambdaSecurityGroup', {
        vpc: props.vpc
      })

      const createDatabasesAndUsersFunction = new NodejsFunction(this, 'function', {
        environment: {
          JOBS_SECRET: this.datastoreJobsSecret.secretName,
          ADMIN_SECRET: datastoreAdminSecret.secretName
        },
        vpc: props.vpc,
        securityGroups: [secGroup],
        bundling: {
          externalModules: [
            "sqlite3",
            "better-sqlite3",
            "mysql",
            "mysql2",
            "oracledb",
            "tedious",
            "pg-query-stream"
          ]
        }
      })

      this.datastoreJobsSecret.grantRead(createDatabasesAndUsersFunction)
      datastoreAdminSecret.grantRead(createDatabasesAndUsersFunction)
      
      encryptionKey.grantDecrypt(createDatabasesAndUsersFunction)

      createDatabasesAndUsersFunction.connections.allowTo(props.datastoreInstance, aws_ec2.Port.tcp(5432))

      new Trigger(this, 'CreateDatabasesTrigger', {
        handler: createDatabasesAndUsersFunction,
      })
    }
  }
}
