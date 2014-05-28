<?php
/**
 * @file
 * frontpage_infobox_feature.features.fe_block_settings.inc
 */

/**
 * Implements hook_default_fe_block_settings().
 */
function frontpage_infobox_feature_default_fe_block_settings() {
  $export = array();

  $export['version'] = '2.0';

  $export['views-infobox-block'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'infobox-block',
    'i18n_block_language' => array(),
    'i18n_mode' => 0,
    'module' => 'views',
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
        'region' => 'top_bar_secondary',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -11,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  return $export;
}
