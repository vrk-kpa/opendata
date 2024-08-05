import {aws_ec2, aws_route53, aws_s3, Duration, Fn, Stack} from 'aws-cdk-lib';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import {ApplicationProtocol, IpAddressType} from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import {Construct} from 'constructs';

import {ElbStackProps} from './elb-stack-props';
import {Subnet} from "aws-cdk-lib/aws-ec2";
import {BucketEncryption} from "aws-cdk-lib/aws-s3";



export class LoadBalancerStack extends Stack {
  readonly loadBalancer: elb.ApplicationLoadBalancer;

  constructor(scope: Construct, id: string, props: ElbStackProps) {
    super(scope, id, props);

    const secGroup = new aws_ec2.SecurityGroup(this, 'loadBalancerSecurityGroup', {
      vpc: props.vpc,
    })

    secGroup.addIngressRule(aws_ec2.Peer.anyIpv4(), aws_ec2.Port.tcp(443), "HTTPS from anywhere")

    const publicSubnetA = Fn.importValue('vpc-SubnetPublicA')
    const publicSubnetB = Fn.importValue('vpc-SubnetPublicB')

    this.loadBalancer = new elb.ApplicationLoadBalancer(this, 'loadBalancer', {
      vpc: props.vpc,
      internetFacing: true,
      ipAddressType: IpAddressType.IPV4,
      vpcSubnets: {
        subnets: [Subnet.fromSubnetId(this, 'subnetA', publicSubnetA), Subnet.fromSubnetId(this, 'subnetB', publicSubnetB)]
      },
      securityGroup: secGroup
    })

    this.loadBalancer.addRedirect({
      sourceProtocol: ApplicationProtocol.HTTP,
      targetProtocol: ApplicationProtocol.HTTPS
    })

    const logBucket = new aws_s3.Bucket(this, 'logBucket', {
      bucketName: `avoindata-${props.environment}-loadbalancer-logs`,
      blockPublicAccess: aws_s3.BlockPublicAccess.BLOCK_ALL,
      encryption: BucketEncryption.S3_MANAGED,
      versioned: true,
      lifecycleRules: [
        {
          enabled: true,
          expiration: Duration.days(30)
        }
      ]
    })

    this.loadBalancer.logAccessLogs(logBucket, this.stackName)

  }
}
