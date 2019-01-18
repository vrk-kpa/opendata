<?php

namespace Drupal\avoindata_infobox\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;

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
    return array(
      '#theme' => 'avoindata_infobox',
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
    );
  }
}
