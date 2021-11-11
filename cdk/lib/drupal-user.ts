import * as cdk from '@aws-cdk/core';
import * as ssm from '@aws-cdk/aws-ssm';
import * as sm from '@aws-cdk/aws-secretsmanager';

export class DrupalUser {
  public user: ssm.IStringParameter;
  public passKey: string;
  public email: ssm.IStringParameter;
  public roles: ssm.IStringParameter;

  constructor(scope: cdk.Construct, environment: string, index: number) {
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