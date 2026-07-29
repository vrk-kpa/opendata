<?php

namespace Drupal\avoindata_hero\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Hero' Block.
 *
 * @Block(
 *   id = "avoindata_hero",
 *   admin_label = @Translation("Avoindata Hero"),
 *   category = @Translation("Avoindata Hero"),
 * )
 */
class HeroBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    $form = \Drupal::formBuilder()->getForm('Drupal\avoindata_hero\Plugin\Form\HeroForm');

    $form['statistics'] = [
      '#lazy_builder' => [\AvoindataHeroHandler::class .
        ':avoindata_hero_ckan_statistics', [],
      ],
      '#create_placeholder' => TRUE,
    ];

    return $form;
  }

}
