<?php
/**
 * @file
 * guide_feature.features.field_base.inc
 */

/**
 * Implements hook_field_default_field_bases().
 */
function guide_feature_field_default_field_bases() {
  $field_bases = array();

  // Exported field_base: 'field_phase'.
  $field_bases['field_phase'] = array(
    'active' => 1,
    'cardinality' => 1,
    'deleted' => 0,
    'entity_types' => array(),
    'field_name' => 'field_phase',
    'indexes' => array(
      'value' => array(
        0 => 'value',
      ),
    ),
    'locked' => 0,
    'module' => 'list',
    'settings' => array(
      'allowed_values' => array(
        'Guide' => 'Guide',
        'Analyze' => 'Analyze',
        'Prepare' => 'Prepare',
        'Follow' => 'Follow',
      ),
      'allowed_values_function' => '',
    ),
    'translatable' => 0,
    'type' => 'list_text',
  );

  return $field_bases;
}
