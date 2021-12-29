export interface EnvProps {
  // docker
  REGISTRY: string,
  REPOSITORY: string,
  // opendata images
  CKAN_IMAGE_TAG: string,
  DRUPAL_IMAGE_TAG: string,
  SOLR_IMAGE_TAG: string,
  NGINX_IMAGE_TAG: string,
  // 3rd party images
  DATAPUSHER_IMAGE_TAG: string,
}

export function parseEnv(key: string): string {
  let val = process.env[key];
  if (val == null) {
    throw new Error(`parseEnv error: ${key} is undefined or null!`);
  }
  return val;
}