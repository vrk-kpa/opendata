## Cloudformation templates

These templates are used for creating AWS cloud environments for development and production.

### The main templates are listed in table below:

Some templates refer to resources created by other templates but currently the stacks do not use Cloudformation imports/exports but the stacks are loosely coupled and references to other stacks are given as template parameters.
| Name | Description | Creation order | Notes |
|---|---|---|---|
| [vpc.yml](./vpc.yml) | Creates AWS VPC  | 1 | can be shared to multiple stacks|
| [database.yml](./database.yml) | Creates persistent resources (RDS and EFS) | 2 | Creates also shared disk despite the name
| [instances.yml](./instances.yml) | Creates application infrastructure (ELB, WAF, Redis, S3, etc )| 3 | Naming is bit misleading as this doesn't create EC2 instances anymore
| [launchtemplate.yml](./launchtemplate.yml) | Creates autoscaling group and launchtemplate | 4 |
| [cloudfront.yml](./cloudfront.yml) | Creates cloudfront distribution | 5 |

### Development and deployment related templates

These templates are not directly part of the application infrastucture but are used for testing and deploying the application.

| Name | Description | Notes |
|---|---|---|
| [ecr.yml](./ecr.yml) | Creates ECR repo for container images|
| [deployments.yml](./deployments.yml) | Creates IAM role for production deployments | |
| [dev_deployments.yml](./dev_deployments.yml) | Creates IAM roles and KMS keys for development deployments| |
| [buildtest_env.yml](./buildtest_env.yml) | Creates resources for environment where builds can be tested |
| [vpc_lockdown.yml](./vpc_lockdown.yml) | Lockdown policies and roles for test build environment |
