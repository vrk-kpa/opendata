<?php

namespace Drupal\avoindata_appfeed\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;

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
    $client = \Drupal::httpClient();
    $currentLang = \Drupal::languageManager()->getCurrentLanguage()->getId();

    try {
      $recentApplicationsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/package_search?fq=dataset_type:showcase&sort=metadata_modified%20desc&rows=3');
      $recentApplicationsResult = Json::decode($recentApplicationsResponse->getBody());
      $recentApplications = $recentApplicationsResult['result']['results'];
    } catch (\Exception $e) {
      $recentApplications = NULL;
    }

    return array(
      '#applications' => $recentApplications,
      '#language' => $currentLang,
      '#theme' => 'avoindata_appfeed',
    );
  }
}
