<?php

namespace Drupal\avoindata_header\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Header' Block.
 *
 * @Block(
 *   id = "avoindata_header",
 *   admin_label = @Translation("Avoindata Header"),
 *   category = @Translation("Avoindata Header"),
 * )
 */
class HeaderBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return [
      '#theme' => 'avoindata_header',
    ];
  }

}
