<?php

namespace Drupal\avoindata_datasetlist\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;

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
    $client = \Drupal::httpClient();
    
    // recently modified datasets
    try {
      $recentDatasetsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/package_search?sort=metadata_modified%20desc&facet.limit=1&rows=5');
      $recentDatasetsResult = Json::decode($recentDatasetsResponse->getBody());
      $recentDatasets = $recentDatasetsResult['result']['results'];
    } catch (\Exception $e) {
      $recentDatasets = NULL;
    }

    // new datasets
    try {
      $newDatasetsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/package_search?sort=metadata_created%20desc&facet.limit=1&rows=5');
      $newDatasetsResult = Json::decode($newDatasetsResponse->getBody());
      $newDatasets = $newDatasetsResult['result']['results'];
    } catch (\Exception $e) {
      $newDatasets = NULL;
    }
    
    // popular datasets
    try {
      $popularDatasetsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/package_search?sort=views_recent%20desc&facet.limit=1&rows=5');
      $popularDatasetsResult = Json::decode($popularDatasetsResponse->getBody());
      $popularDatasets = $popularDatasetsResult['result']['results'];
    } catch (\Exception $e) {
      $popularDatasets = NULL;
    }
    
    return array(
      '#recentdatasets' => $recentDatasets,
      '#newdatasets' => $newDatasets,
      '#populardatasets' => $popularDatasets,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_datasetlist',
    );
  }
}
