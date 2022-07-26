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

    $form['datasetcount'] = [
      '#lazy_builder' => [\AvoindataHeroHandler::class .
        ':avoindata_hero_dataset_count', [],
      ],
      '#create_placeholder' => TRUE,
    ];

    $form['organizationcount'] = [
      '#lazy_builder' => [\AvoindataHeroHandler::class .
        ':avoindata_hero_organization_count', [],
      ],
      '#create_placeholder' => TRUE,
    ];

    $form['applicationcount'] = [
      '#lazy_builder' => [\AvoindataHeroHandler::class .
        ':avoindata_hero_application_count', [],
      ],
      '#create_placeholder' => TRUE,
    ];

    return $form;
  }

}
