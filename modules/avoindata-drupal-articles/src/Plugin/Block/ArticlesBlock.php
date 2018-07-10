<?php

namespace Drupal\avoindata_articles\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;

/**
 * Provides a 'Avoindata Articles' Block.
 *
 * @Block(
 *   id = "avoindata_articles",
 *   admin_label = @Translation("Avoindata Articles"),
 *   category = @Translation("Avoindata Articles"),
 * )
 */
class ArticlesBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return array(
      '#theme' => 'avoindata_articles',
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
    );
  }
}
