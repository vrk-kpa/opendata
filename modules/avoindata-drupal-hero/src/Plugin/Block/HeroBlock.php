<?php

namespace Drupal\avoindata_hero\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Core\Form\FormInterface;

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
    return $form;
  }

}
