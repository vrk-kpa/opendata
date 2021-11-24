import * as cdk from '@aws-cdk/core';
import * as ecr from '@aws-cdk/aws-ecr';

export class RegistryStack extends cdk.Stack {
  readonly nginxRepository: ecr.IRepository;
  readonly drupalRepository: ecr.IRepository;
  readonly ckanRepository: ecr.IRepository;
  readonly datapusherRepository: ecr.IRepository;
  readonly solrRepository: ecr.IRepository;

  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.nginxRepository = new ecr.Repository(this, 'nginxRepository', {
      repositoryName: 'opendata/nginx',
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
    });

    this.drupalRepository = new ecr.Repository(this, 'drupalRepository', {
      repositoryName: 'opendata/drupal',
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
    });

    this.ckanRepository = new ecr.Repository(this, 'ckanRepository', {
      repositoryName: 'opendata/ckan',
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
    });

    this.datapusherRepository = new ecr.Repository(this, 'datapusherRepository', {
      repositoryName: 'opendata/datapusher',
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
    });

    this.solrRepository = new ecr.Repository(this, 'solrRepository', {
      repositoryName: 'opendata/solr',
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
    });
  }
}
