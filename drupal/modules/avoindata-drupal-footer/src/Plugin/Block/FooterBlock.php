<?php

namespace Drupal\avoindata_footer\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Footer' Block.
 *
 * @Block(
 *   id = "avoindata_footer",
 *   admin_label = @Translation("Avoindata Footer"),
 *   category = @Translation("Avoindata Footer"),
 * )
 */
class FooterBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return [
      '#theme' => 'avoindata_footer',
    ];
  }

}
