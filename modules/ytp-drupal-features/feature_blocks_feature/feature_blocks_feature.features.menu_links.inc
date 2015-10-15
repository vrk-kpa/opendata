<?php
/**
 * @file
 * feature_blocks_feature.features.menu_links.inc
 */

/**
 * Implements hook_menu_default_menu_links().
 */
function feature_blocks_feature_menu_default_menu_links() {
  $menu_links = array();

  // Exported menu link: management_twitter-block:admin/config/system/twitter-block.
  $menu_links['management_twitter-block:admin/config/system/twitter-block'] = array(
    'menu_name' => 'management',
    'link_path' => 'admin/config/system/twitter-block',
    'router_path' => 'admin/config/system/twitter-block',
    'link_title' => 'Twitter Block',
    'options' => array(
      'attributes' => array(
        'title' => 'Configure cache settings for Twitter blocks.',
      ),
      'alter' => TRUE,
      'identifier' => 'management_twitter-block:admin/config/system/twitter-block',
    ),
    'module' => 'system',
    'hidden' => 0,
    'external' => 0,
    'has_children' => 0,
    'expanded' => 0,
    'weight' => 0,
    'customized' => 0,
    'language' => 'und',
    'menu_links_customized' => 0,
    'parent_identifier' => 'management_system:admin/config/system',
  );

  // Translatables
  // Included for use with string extractors like potx.
  t('Twitter Block');

  return $menu_links;
}
