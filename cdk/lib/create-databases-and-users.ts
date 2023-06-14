import {Construct} from "constructs";
import {NodejsFunction} from "aws-cdk-lib/aws-lambda-nodejs";
import {aws_ec2, aws_rds} from "aws-cdk-lib";
import {CreateDatabasesAndUsersProps} from "./create-databases-and-users-props";


export class CreateDatabasesAndUsers extends Construct {
  constructor(scope: Construct, id: string, props: CreateDatabasesAndUsersProps) {
    super(scope, id);

    const datastoreSecret = new aws_rds.DatabaseSecret(this, "datastoreJobsSecret", {
      username: "datastore_jobs"
    })

    const datastoreAdminSecret = props.datastoreCredentials.secret

    if (datastoreAdminSecret?.secretName !== undefined) {

      const secGroup = new aws_ec2.SecurityGroup(this, 'LambdaSecurityGroup', {
        vpc: props.vpc
      })

      const createDatabasesAndUsersFunction = new NodejsFunction(this, 'function', {
        environment: {
          SECRET_NAME: datastoreSecret.secretName,
          ADMIN_SECRET: datastoreAdminSecret.secretName
        },
        vpc: props.vpc,
        securityGroups: [secGroup]
      })

      datastoreSecret.grantRead(createDatabasesAndUsersFunction)
      datastoreAdminSecret.grantRead(createDatabasesAndUsersFunction)

      createDatabasesAndUsersFunction.connections.allowTo(props.datastoreInstance, aws_ec2.Port.tcp(5432))
    }
  }
}
