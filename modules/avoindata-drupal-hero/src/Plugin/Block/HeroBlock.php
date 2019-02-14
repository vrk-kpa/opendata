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
      '#lazy_builder' => ['avoindata_hero_datasetCount', []],
      '#create_placeholder' => TRUE,
    ];

    $form['organizationcount'] = [
      '#lazy_builder' => ['avoindata_hero_organizationCount', []],
      '#create_placeholder' => TRUE,
    ];

    $form['applicationcount'] = [
      '#lazy_builder' => ['avoindata_hero_applicationCount', []],
      '#create_placeholder' => TRUE,
    ];

    return $form;
  }

}
