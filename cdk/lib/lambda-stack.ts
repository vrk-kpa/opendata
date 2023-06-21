import {CreateDatabasesAndUsers} from "./create-databases-and-users";
import {aws_ec2, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {LambdaStackProps} from "./lambda-stack-props";

export class LambdaStack extends Stack {
  constructor(scope: Construct, id: string, props: LambdaStackProps ) {
    super(scope, id, props);
    const lambda = new CreateDatabasesAndUsers(this, 'create-databases-and-users', {
      datastoreInstance: props.datastoreInstance,
      datastoreCredentials: props.datastoreCredentials,
      vpc: props.vpc,
      envProps: props.envProps,
      env: props.env,
      environment: props.environment,
      fqdn: props.fqdn,
      secondaryFqdn: props.secondaryFqdn,
      domainName: props.domainName,
      secondaryDomainName: props.secondaryDomainName,
    })
  }
}
