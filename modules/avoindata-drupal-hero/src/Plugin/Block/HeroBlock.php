<?php

namespace Drupal\avoindata_hero\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Hero' Block.
 *
 * @Block(
 *   id = "avoindata_hero",
 *   admin_label = @Translation("Hero"),
 *   category = @Translation("Hero"),
 * )
 */
class HeroBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return array(
      '#theme' => 'avoindata_hero',
    );
  }

}
