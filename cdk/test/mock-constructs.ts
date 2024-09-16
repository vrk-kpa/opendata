import { EnvProps } from '../lib/env-props';

export const mockEnv = {
  account: '156418131626',
  region: 'eu-west-1',
};

export const mockEnvProps: EnvProps = {
  // docker
  REGISTRY: 'some.mock.registry',
  REPOSITORY: 'opendata',
  // opendata images
  CKAN_IMAGE_TAG: 'v0.0.0',
  DRUPAL_IMAGE_TAG: 'v0.0.0',
  SOLR_IMAGE_TAG: 'v0.0.0',
  DATAPUSHER_IMAGE_TAG: 'v0.0.0',
  NGINX_IMAGE_TAG: 'v0.0.0',
  CLAMAV_IMAGE_TAG: 'v0.0.0',
  // 3rd party images
  FUSEKI_IMAGE_TAG: 'v0.0.0',
};
