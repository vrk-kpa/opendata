<?php

namespace Drupal\avoindata_explore\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata external' Block.
 *
 * @Block(
 *   id = "avoindata_external",
 *   admin_label = @Translation("Avoindata External"),
 *   category = @Translation("Avoindata External"),
 * )
 */
class ExternalBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return [
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_external',
    ];
  }

}
