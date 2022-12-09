<?php

namespace Drupal\avoindata_header\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Search Block.
 *
 * @Block(
 *   id = "avoindata_search",
 *   admin_label = @Translation("Avoindata Search"),
 *   category = @Translation("Avoindata Search"),
 * )
 */
class SearchBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {

    $form = \Drupal::formBuilder()->getForm('Drupal\avoindata_header\Plugin\Form\SearchForm');

    return $form;
  }

}
