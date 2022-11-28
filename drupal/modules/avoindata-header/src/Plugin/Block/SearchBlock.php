<?php

namespace Drupal\avoindata_header\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Search Block.
 *
 * @Block(
 *   id = "avoindata_serach",
 *   admin_label = @Translation("Avoindata Search"),
 *   category = @Translation("Avoindata Search"),
 * )
 */
class SearchBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {

    return [
      '#theme' => 'avoindata_search',
    ];
  }

}