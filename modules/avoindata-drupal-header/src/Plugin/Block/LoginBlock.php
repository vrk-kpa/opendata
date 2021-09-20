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
    $avoindata_drupal_username = [
      '#lazy_builder' => [\AvoindataHeaderHandler::class .
        ':avoindata_drupal_username', [],
      ],
      '#create_placeholder' => TRUE,
    ];

    return [
      '#avoindata_drupal_username' => $avoindata_drupal_username,
      '#theme' => 'avoindata_login',
    ];
  }

}
