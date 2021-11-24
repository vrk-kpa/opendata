import * as cdk from '@aws-cdk/core';
import * as ecs from '@aws-cdk/aws-ecs';
import * as ssm from '@aws-cdk/aws-ssm';
import * as sm from '@aws-cdk/aws-secretsmanager';

// NOTE: these are not currently used because it's unclear how construct ID's would behave...
//       perhaps the ID's must be given separately, but that would nullify the usefulness of these funcs

export function getParam(scope: cdk.Construct, name: string): ssm.IStringParameter {
  return ssm.StringParameter.fromStringParameterAttributes(scope, name, {
    parameterName: name,
  });
}

export function getSecret(scope: cdk.Construct, name: string): sm.ISecret {
  return sm.Secret.fromSecretNameV2(scope, name, name);
}

export function getEcsSecret(scope: cdk.Construct, name: string): ecs.Secret {
  return ecs.Secret.fromSecretsManager(getSecret(scope, name));
}
