<?php

namespace Drupal\avoindata_datasetlist\Plugin\Block;

use Drupal\Core\Block\BlockBase;

/**
 * Provides a 'Avoindata Dataset List' Block.
 *
 * @Block(
 *   id = "avoindata_datasetlist",
 *   admin_label = @Translation("Avoindata Dataset List"),
 *   category = @Translation("Avoindata Dataset List"),
 * )
 */
class DatasetlistBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {

    // Recently modified datasets.
    $recentDatasets = [
      '#lazy_builder' => ['avoindata_recent_datasets', []],
      '#create_placeholder' => TRUE,
    ];

    // New datasets.
    $newDatasets = [
      '#lazy_builder' => ['avoindata_new_datasets', []],
      '#create_placeholder' => TRUE,
    ];

    // Popular datasets.
    $popularDatasets = [
      '#lazy_builder' => ['avoindata_popular_datasets', []],
      '#create_placeholder' => TRUE,
    ];

    return [
      '#recentdatasets' => $recentDatasets,
      '#newdatasets' => $newDatasets,
      '#populardatasets' => $popularDatasets,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_datasetlist',
    ];
  }

}
