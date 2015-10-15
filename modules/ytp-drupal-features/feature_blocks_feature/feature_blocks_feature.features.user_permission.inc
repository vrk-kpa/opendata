<?php
/**
 * @file
 * feature_blocks_feature.features.user_permission.inc
 */

/**
 * Implements hook_user_default_permissions().
 */
function feature_blocks_feature_user_default_permissions() {
  $permissions = array();

  // Exported permission: 'administer twitter block'.
  $permissions['administer twitter block'] = array(
    'name' => 'administer twitter block',
    'roles' => array(
      'administrator' => 'administrator',
    ),
    'module' => 'twitter_block',
  );

  return $permissions;
}
