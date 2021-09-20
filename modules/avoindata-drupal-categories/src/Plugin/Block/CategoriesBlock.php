<?php

namespace Drupal\avoindata_categories\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Categories' Block.
 *
 * @Block(
 *   id = "avoindata_categories",
 *   admin_label = @Translation("Avoindata Categories"),
 *   category = @Translation("Avoindata Categories"),
 * )
 */
class CategoriesBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    $categories = [
      '#lazy_builder' => [\AvoindataCategoriesHandler::class .
        ':avoindata_categories', [],
      ],
      '#create_placeholder' => FALSE,
    ];

    return [
      '#categories' => $categories,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_categories',
    ];
  }

}
