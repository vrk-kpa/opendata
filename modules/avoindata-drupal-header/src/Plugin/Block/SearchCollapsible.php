<?php

namespace Drupal\avoindata_header\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a collapsible search field that's used in header.
 *
 * @Block(
 *   id = "search_collapsible",
 *   admin_label = @Translation("Collapsible search"),
 *   category = @Translation("Search"),
 * )
 */
class SearchCollapsible extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return array(
      '#theme' => 'avoindata_header_search_collapsible',
    );
  }

}