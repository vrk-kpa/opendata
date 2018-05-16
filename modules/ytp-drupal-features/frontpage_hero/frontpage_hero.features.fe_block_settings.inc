<?php
/**
 * @file
 * frontpage_hero.features.fe_block_settings.inc
 */

/**
 * Implements hook_default_fe_block_settings().
 */
function frontpage_hero_default_fe_block_settings() {
  $export = array();

  $export['version'] = '2.0';

  $export['ytp_frontpage-hero'] = array(
    'cache' => -1,
    'custom' => 0,
    'delta' => 'hero',
    'i18n_block_language' => array(),
    'i18n_mode' => 0,
    'module' => 'ytp_frontpage',
    'node_types' => array(),
    'pages' => '',
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
        'region' => 'hero',
        'status' => 1,
        'theme' => 'ytp_theme',
        'weight' => 0,
      ),
    ),
    'title' => '',
    'visibility' => 0,
  );

  return $export;
}
