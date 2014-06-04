<?php
/**
 * @file
 * frontpage_tutorial.features.field_base.inc
 */

/**
 * Implements hook_field_default_field_bases().
 */
function frontpage_tutorial_field_default_field_bases() {
  $field_bases = array();

  // Exported field_base: 'field_role'
  $field_bases['field_role'] = array(
    'active' => 1,
    'cardinality' => 1,
    'deleted' => 0,
    'entity_types' => array(),
    'field_name' => 'field_role',
    'foreign keys' => array(),
    'indexes' => array(
      'value' => array(
        0 => 'value',
      ),
    ),
    'locked' => 0,
    'module' => 'list',
    'settings' => array(
      'allowed_values' => array(
        'Anonymous' => 'Anonymous',
        'Authenticated' => 'Authenticated',
        'In organization' => 'In organization',
      ),
      'allowed_values_function' => '',
    ),
    'translatable' => 0,
    'type' => 'list_text',
  );

  return $field_bases;
}
