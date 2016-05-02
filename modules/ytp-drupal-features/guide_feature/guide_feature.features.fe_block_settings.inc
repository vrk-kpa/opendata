<?php
/**
 * @file
 * guide_feature.features.fe_block_settings.inc
 */

/**
 * Implements hook_default_fe_block_settings().
 */
function guide_feature_default_fe_block_settings() {
  $export = array();

  $export['version'] = '2.0';

  $export['views-guide_view-block'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'guide_view-block',
    'i18n_block_language' => array(),
    'i18n_mode' => 0,
    'module' => 'views',
    'node_types' => array(),
    'pages' => 'opas/kartoita',
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
        'region' => 'content',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -18,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  $export['views-guide_view-block_1'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'guide_view-block_1',
    'i18n_block_language' => array(),
    'i18n_mode' => 0,
    'module' => 'views',
    'node_types' => array(),
    'pages' => 'opas/analysoi',
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
        'region' => 'content',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -17,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  $export['views-guide_view-block_2'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'guide_view-block_2',
    'i18n_block_language' => array(),
    'i18n_mode' => 0,
    'module' => 'views',
    'node_types' => array(),
    'pages' => 'opas/valmistele',
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
        'region' => 'content',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -16,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  $export['views-guide_view-block_3'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'guide_view-block_3',
    'i18n_block_language' => array(),
    'i18n_mode' => 0,
    'module' => 'views',
    'node_types' => array(),
    'pages' => 'opas/seuraa',
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
        'region' => 'content',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -15,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  return $export;
}
