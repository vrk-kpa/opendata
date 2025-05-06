import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';

import { ClusterStack } from '../lib/cluster-stack';
import { LoadBalancerStack } from '../lib/load-balancer-stack';
import { mockEnv, mockEnvProps } from './mock-constructs';
import {CertificateStack} from "../lib/certificate-stack";

test('verify load balancer stack resources', () => {
  const app = new cdk.App();
  const clusterStack = new ClusterStack(app, 'ClusterStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpcId: 'someid'
  });
  
  // WHEN
  const stack = new LoadBalancerStack(app, 'LoadBalancerStack-test', {
    env: mockEnv,
    environment: 'mock-env',
    vpc: clusterStack.vpc,
    fqdn: 'localhost',
    secondaryFqdn: 'localhost',
    domainName: 'mock.localhost',
    secondaryDomainName: 'mock.localhost',

  });
  // THEN
  // no actual resources to verify
});
