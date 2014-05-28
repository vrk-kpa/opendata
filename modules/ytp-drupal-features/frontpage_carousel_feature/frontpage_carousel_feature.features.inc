<?php
/**
 * @file
 * frontpage_carousel_feature.features.inc
 */

/**
 * Implements hook_ctools_plugin_api().
 */
function frontpage_carousel_feature_ctools_plugin_api($module = NULL, $api = NULL) {
  if ($module == "strongarm" && $api == "strongarm") {
    return array("version" => "1");
  }
}

/**
 * Implements hook_views_api().
 */
function frontpage_carousel_feature_views_api($module = NULL, $api = NULL) {
  return array("api" => "3.0");
}

/**
 * Implements hook_node_info().
 */
function frontpage_carousel_feature_node_info() {
  $items = array(
    'carousel_item' => array(
      'name' => t('Carousel item'),
      'base' => 'node_content',
      'description' => t('Front page carousel content'),
      'has_title' => '1',
      'title_label' => t('Title'),
      'help' => '',
    ),
  );
  return $items;
}
