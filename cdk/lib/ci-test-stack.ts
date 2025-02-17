import {aws_iam, aws_s3, Duration, Stack} from "aws-cdk-lib";
import {Construct} from "constructs";
import {CiTestStackProps} from "./ci-test-stack-props";

export class CiTestStack extends Stack {
  constructor(scope: Construct, id: string, props: CiTestStackProps) {
    super(scope, id, props);

    const testBucket = new aws_s3.Bucket(this,'TestBucket', {
      bucketName: props.testBucketName,
      blockPublicAccess: aws_s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          expiration: Duration.days(1)
        }
      ]
    })

    const oidcProviderArn = Stack.of(this).formatArn({
        region: "",
        partition: "aws",
        resource: "oidc-provider",
        service: "iam",
        resourceName: "token.actions.githubusercontent.com"
      })

    const testRole = new aws_iam.Role(this, 'TestRole', {
      assumedBy: new aws_iam.WebIdentityPrincipal(oidcProviderArn, {
          StringLike: {
            "token.actions.githubusercontent.com:sub": [
              `repo:${props.githubOrg}/${props.githubRepo}:*`,
              `repo:${props.githubOrg}/${props.githubRepo2}:*`]
          }
      })
    })

    testBucket.grantWrite(testRole)
    testBucket.grantRead(testRole)
  }

}
