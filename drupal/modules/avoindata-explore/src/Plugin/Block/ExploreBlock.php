<?php

namespace Drupal\avoindata_explore\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata explore' Block.
 *
 * @Block(
 *   id = "avoindata_explore",
 *   admin_label = @Translation("Avoindata Explore"),
 *   category = @Translation("Avoindata Explore"),
 * )
 */
class ExploreBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return [
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_explore',
    ];
  }

}
