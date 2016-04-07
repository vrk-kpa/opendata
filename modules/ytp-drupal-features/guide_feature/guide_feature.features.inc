<?php
/**
 * @file
 * guide_feature.features.inc
 */

/**
 * Implements hook_ctools_plugin_api().
 */
function guide_feature_ctools_plugin_api($module = NULL, $api = NULL) {
  if ($module == "strongarm" && $api == "strongarm") {
    return array("version" => "1");
  }
}

/**
 * Implements hook_views_api().
 */
function guide_feature_views_api($module = NULL, $api = NULL) {
  return array("api" => "3.0");
}

/**
 * Implements hook_node_info().
 */
function guide_feature_node_info() {
  $items = array(
    'guide_accordion' => array(
      'name' => t('Guide Accordion'),
      'base' => 'node_content',
      'description' => t('Accordion elements for open data guide'),
      'has_title' => '1',
      'title_label' => t('Title'),
      'help' => '',
    ),
  );
  drupal_alter('node_info', $items);
  return $items;
}
