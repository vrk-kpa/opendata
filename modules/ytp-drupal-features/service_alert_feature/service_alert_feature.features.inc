<?php
/**
 * @file
 * service_alert_feature.features.inc
 */

/**
 * Implements hook_views_api().
 */
function service_alert_feature_views_api($module = NULL, $api = NULL) {
  return array("api" => "3.0");
}

/**
 * Implements hook_node_info().
 */
function service_alert_feature_node_info() {
  $items = array(
    'service_alert' => array(
      'name' => t('Service alert'),
      'base' => 'node_content',
      'description' => t('Service alerts are messages that are shown on every page.'),
      'has_title' => '1',
      'title_label' => t('Title'),
      'help' => '',
    ),
  );
  return $items;
}
