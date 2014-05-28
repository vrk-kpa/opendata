<?php
/**
 * @file
 * frontpage_infobox_feature.features.inc
 */

/**
 * Implements hook_ctools_plugin_api().
 */
function frontpage_infobox_feature_ctools_plugin_api($module = NULL, $api = NULL) {
  if ($module == "strongarm" && $api == "strongarm") {
    return array("version" => "1");
  }
}

/**
 * Implements hook_views_api().
 */
function frontpage_infobox_feature_views_api($module = NULL, $api = NULL) {
  return array("api" => "3.0");
}

/**
 * Implements hook_node_info().
 */
function frontpage_infobox_feature_node_info() {
  $items = array(
    'infobox' => array(
      'name' => t('Infobox'),
      'base' => 'node_content',
      'description' => t('Front page infobox content'),
      'has_title' => '1',
      'title_label' => t('Title'),
      'help' => '',
    ),
  );
  return $items;
}
