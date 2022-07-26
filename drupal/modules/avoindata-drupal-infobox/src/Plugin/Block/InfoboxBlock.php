<?php

namespace Drupal\avoindata_infobox\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Infobox' Block.
 *
 * @Block(
 *   id = "avoindata_infobox",
 *   admin_label = @Translation("Avoindata Infobox"),
 *   category = @Translation("Avoindata Infobox"),
 * )
 */
class InfoboxBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return [
      '#theme' => 'avoindata_infobox',
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
    ];
  }

}
