<?php
/**
 * @file
 * feature_blocks_feature.features.fe_block_settings.inc
 */

/**
 * Implements hook_default_fe_block_settings().
 */
function feature_blocks_feature_default_fe_block_settings() {
  $export = array();

  $export['version'] = '2.0';

  $export['block-latest_datasets'] = array(
    'cache' => -1,
    'custom' => 0,
    'i18n_block_language' => array(),
    'i18n_mode' => 1,
    'machine_name' => 'latest_datasets',
    'module' => 'block',
    'node_types' => array(),
    'pages' => '<front>',
    'roles' => array(),
    'themes' => array(
      'bartik' => array(
        'region' => '',
        'status' => 0,
        'theme' => 'bartik',
        'weight' => 0,
      ),
      'bootstrap' => array(
        'region' => '',
        'status' => 0,
        'theme' => 'bootstrap',
        'weight' => 0,
      ),
      'seven' => array(
        'region' => '',
        'status' => 0,
        'theme' => 'seven',
        'weight' => 0,
      ),
      'ytp_theme' => array(
        'region' => 'feature_blocks',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -17,
      ),
    ),
    'title' => 'Latest datasets',
    'visibility' => 1,
  );

  $export['block-popular_datasets'] = array(
    'cache' => -1,
    'custom' => 0,
    'i18n_block_language' => array(),
    'i18n_mode' => 1,
    'machine_name' => 'popular_datasets',
    'module' => 'block',
    'node_types' => array(),
    'pages' => '<front>',
    'roles' => array(),
    'themes' => array(
      'bartik' => array(
        'region' => '',
        'status' => 0,
        'theme' => 'bartik',
        'weight' => 0,
      ),
      'bootstrap' => array(
        'region' => '',
        'status' => 0,
        'theme' => 'bootstrap',
        'weight' => 0,
      ),
      'seven' => array(
        'region' => '',
        'status' => 0,
        'theme' => 'seven',
        'weight' => 0,
      ),
      'ytp_theme' => array(
        'region' => 'feature_blocks',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -16,
      ),
    ),
    'title' => 'Most popular datasets',
    'visibility' => 1,
  );

  return $export;
}
