<?php

namespace Drupal\avoindata_footer\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;

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
    return array(
      '#theme' => 'avoindata_footer',
    );
  }
}

