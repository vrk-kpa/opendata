<?php

namespace Drupal\avoindata_appfeed\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata App Feed' Block.
 *
 * @Block(
 *   id = "avoindata_appfeed",
 *   admin_label = @Translation("Avoindata App Feed"),
 *   category = @Translation("Avoindata App Feed"),
 * )
 */
class AppFeedBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {

    $recentApplications = [
      '#lazy_builder' => [\AvoindataApplicationHandler::class .
        ':avoindata_recent_applications', [],
      ],
      '#create_placeholder' => FALSE,
    ];

    return [
      '#applications' => $recentApplications,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_appfeed',
    ];
  }

}
