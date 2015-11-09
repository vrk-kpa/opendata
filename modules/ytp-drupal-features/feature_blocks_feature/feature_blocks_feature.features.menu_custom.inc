<?php
/**
 * @file
 * feature_blocks_feature.features.menu_custom.inc
 */

/**
 * Implements hook_menu_default_menu_custom().
 */
function feature_blocks_feature_menu_default_menu_custom() {
  $menus = array();

  // Exported menu: management.
  $menus['management'] = array(
    'menu_name' => 'management',
    'title' => 'Management',
    'description' => 'The <em>Management</em> menu contains links for administrative tasks.',
    'language' => 'und',
    'i18n_mode' => 0,
  );
  // Exported menu: menu-related-sites.
  $menus['menu-related-sites'] = array(
    'menu_name' => 'menu-related-sites',
    'title' => 'Related sites',
    'description' => 'Links to related sites are shown in a block on front page.',
    'language' => 'und',
    'i18n_mode' => 5,
  );
  // Translatables
  // Included for use with string extractors like potx.
  t('Links to related sites are shown in a block on front page.');
  t('Management');
  t('Related sites');
  t('The <em>Management</em> menu contains links for administrative tasks.');

  return $menus;
}
