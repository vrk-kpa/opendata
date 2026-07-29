<?php

namespace Drupal\avoindata_explore\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata support' Block.
 *
 * @Block(
 *   id = "avoindata_support",
 *   admin_label = @Translation("Avoindata Support"),
 *   category = @Translation("Avoindata Support"),
 * )
 */
class SupportBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return [
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_support',
    ];
  }

}
