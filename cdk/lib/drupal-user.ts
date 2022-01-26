import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';

export class DrupalUser {
  public user: ssm.IStringParameter;
  public passKey: string;
  public email: ssm.IStringParameter;
  public roles: ssm.IStringParameter;

  constructor(scope: Construct, environment: string, index: number) {
    this.user = ssm.StringParameter.fromStringParameterAttributes(scope, `pDrupalUser${index}User`, {
      parameterName: `/${environment}/opendata/common/users/${index}/user`,
    });
    this.passKey = `user_${index}_pass`;
    this.email = ssm.StringParameter.fromStringParameterAttributes(scope, `pDrupalUser${index}Email`, {
      parameterName: `/${environment}/opendata/common/users/${index}/email`,
    });
    this.roles = ssm.StringParameter.fromStringParameterAttributes(scope, `pDrupalUser${index}Roles`, {
      parameterName: `/${environment}/opendata/common/users/${index}/roles`,
    });
  }
}