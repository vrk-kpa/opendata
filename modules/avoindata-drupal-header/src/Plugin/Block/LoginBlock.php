<?php

namespace Drupal\avoindata_header\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Login Block.
 *
 * @Block(
 *   id = "avoindata_login",
 *   admin_label = @Translation("Avoindata Login"),
 *   category = @Translation("Avoindata Login"),
 * )
 */
class LoginBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    return [
      '#theme' => 'avoindata_login',
    ];
  }

}
