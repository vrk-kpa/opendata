<?php
/**
 * @file
 * blocks_feature.features.fe_block_boxes.inc
 */

/**
 * Implements hook_default_fe_block_boxes().
 */
function blocks_feature_default_fe_block_boxes() {
  $export = array();

  $fe_block_boxes = new stdClass();
  $fe_block_boxes->info = 'Search Box';
  $fe_block_boxes->format = 'full_html';
  $fe_block_boxes->machine_name = 'search_box';
  $fe_block_boxes->body = '<p>Frontpage search box</p>';

  $export['search_box'] = $fe_block_boxes;

  return $export;
}
