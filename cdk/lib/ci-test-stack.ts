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



    const oicdProvider = new aws_iam.OpenIdConnectProvider(this,  'oicdProvider', {
      url: 'https://token.actions.githubusercontent.com',
      clientIds: ['sts.amazonaws.com']
    })

    const testRole = new aws_iam.Role(this, 'TestRole', {
      assumedBy: new aws_iam.FederatedPrincipal(oicdProvider.openIdConnectProviderArn, {
          StringLike: {
            "token.actions.githubusercontent.com:sub": `repo:${props.githubOrg}/${props.githubRepo}:*`
          }
      })
    })

    testBucket.grantWrite(testRole)
  }

}
