<?php
/**
 * @file
 * frontpage_tutorial.features.inc
 */

/**
 * Implements hook_ctools_plugin_api().
 */
function frontpage_tutorial_ctools_plugin_api($module = NULL, $api = NULL) {
  if ($module == "strongarm" && $api == "strongarm") {
    return array("version" => "1");
  }
}

/**
 * Implements hook_views_api().
 */
function frontpage_tutorial_views_api($module = NULL, $api = NULL) {
  return array("api" => "3.0",
    'path' => drupal_get_path('module', 'frontpage_tutorial'),
    'template path' => drupal_get_path('module', 'frontpage_tutorial'),);

}

/**
 * Implements hook_node_info().
 */
function frontpage_tutorial_node_info() {
  $items = array(
    'tutorial' => array(
      'name' => t('Tutorial'),
      'base' => 'node_content',
      'description' => t('Content for frontpage tutorial box'),
      'has_title' => '1',
      'title_label' => t('Title'),
      'help' => '',
    ),
  );
  drupal_alter('node_info', $items);
  return $items;
}
