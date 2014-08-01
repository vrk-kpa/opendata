<?php
/**
 * @file
 * frontpage_tutorial.features.fe_block_settings.inc
 */

/**
 * Implements hook_default_fe_block_settings().
 */
function frontpage_tutorial_default_fe_block_settings() {
  $export = array();

  $export['version'] = '2.0';

  $export['views-e47fa3088ec33a576aec69631d43e97b'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'e47fa3088ec33a576aec69631d43e97b',
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
        'region' => 'sidebar_second',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -14,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  $export['views-e4be4f0f303377307ca9418c650dc0ba'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'e4be4f0f303377307ca9418c650dc0ba',
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
        'region' => 'disabled',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -13,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  $export['views-edd31d26be0b66ec9af4c7fd260f7efa'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'edd31d26be0b66ec9af4c7fd260f7efa',
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
        'region' => 'sidebar_second',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => -13,
      ),
    ),
    'title' => '',
    'visibility' => 1,
  );

  return $export;
}
