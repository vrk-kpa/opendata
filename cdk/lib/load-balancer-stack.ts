import {aws_ec2, aws_s3, Duration, Fn, Stack} from 'aws-cdk-lib';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import {IpAddressType} from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import {Construct} from 'constructs';

import {ElbStackProps} from './elb-stack-props';
import {Peer, Port, Subnet} from "aws-cdk-lib/aws-ec2";
import {BucketEncryption} from "aws-cdk-lib/aws-s3";
import {StringParameter} from "aws-cdk-lib/aws-ssm";
import {CfnWebACLAssociation} from "aws-cdk-lib/aws-wafv2";


export class LoadBalancerStack extends Stack {
  readonly loadBalancer: elb.ApplicationLoadBalancer;

  constructor(scope: Construct, id: string, props: ElbStackProps) {
    super(scope, id, props);

    // get params

    const allowedIp1 = StringParameter.fromStringParameterName(this, 'allowedIp1',
      `/${props.environment}/opendata/cdk/lb_allowed_ip_1`)

    const allowedIp2 = StringParameter.fromStringParameterName(this, 'allowedIp2',
      `/${props.environment}/opendata/cdk/lb_allowed_ip_2`)

    const allowedIp3 = StringParameter.fromStringParameterName(this, 'allowedIp3',
      `/${props.environment}/opendata/cdk/lb_allowed_ip_3`)

    const allowedIp4 = StringParameter.fromStringParameterName(this, 'allowedIp4',
      `/${props.environment}/opendata/cdk/lb_allowed_ip_4`)

    const secGroup = new aws_ec2.SecurityGroup(this, 'loadBalancerSecurityGroup', {
      vpc: props.vpc,
    })

    // pl-4fa04526 is com.amazonaws.global.cloudfront.origin-facing
    secGroup.addIngressRule(Peer.prefixList('pl-4fa04526'), Port.tcp(443))

    secGroup.addIngressRule(Peer.ipv4(allowedIp1.stringValue), Port.tcp(443))
    secGroup.addIngressRule(Peer.ipv4(allowedIp2.stringValue), Port.tcp(443))
    secGroup.addIngressRule(Peer.ipv4(allowedIp3.stringValue), Port.tcp(443))
    secGroup.addIngressRule(Peer.ipv4(allowedIp4.stringValue), Port.tcp(443))

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
