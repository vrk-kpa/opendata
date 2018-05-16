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
    $recentDatasetsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/package_search?sort=metadata_modified%20desc&facet.limit=1&rows=5');
    $recentDatasetsResult = Json::decode($recentDatasetsResponse->getBody());
    $recentDatasets = $recentDatasetsResult['result']['results'];
    // new datasets
    $newDatasetsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/package_search?sort=metadata_created%20desc&facet.limit=1&rows=5');
    $newDatasetsResult = Json::decode($newDatasetsResponse->getBody());
    $newDatasets = $newDatasetsResult['result']['results'];
    // // popular datasets
    $popularDatasetsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/package_search?sort=views_recent%20desc&facet.limit=1&rows=5');
    $popularDatasetsResult = Json::decode($popularDatasetsResponse->getBody());
    $popularDatasets = $popularDatasetsResult['result']['results'];
    
    return array(
      '#recentdatasets' => $recentDatasets,
      '#newdatasets' => $newDatasets,
      '#populardatasets' => $popularDatasets,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_datasetlist',
    );
  }
}
