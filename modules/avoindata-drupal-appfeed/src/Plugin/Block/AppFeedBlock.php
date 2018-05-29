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

    // Limit not working for ckanext_showcase_list
    $recentApplicationsResponse = $client->request('GET', 'http://localhost:8080/data/api/action/ckanext_showcase_list?sort=metadata_modified%20desc');
    $recentApplicationsResult = Json::decode($recentApplicationsResponse->getBody());
    $recentApplications = $recentApplicationsResult['result'];
    $recentApplications = array_slice($recentApplications, 0, 3);

    // TODO: find more elegant way of doing this.
    foreach ($recentApplications as &$application) {
      $extras = $application['extras'];
      foreach ($extras as $item) {
        	if ($item['key'] == 'icon') {
            $application['logourl'] = $item['value'];
          }
          elseif ($item['key'] == 'category') {
            $application['category'] = (array) json_decode($item['value']);
          }
          elseif ($item['key'] == 'notes_translated') {
            $application['notes'] = (array) json_decode($item['value']);
          }
      }
    }
    unset($application);

    return array(
      '#applications' => $recentApplications,
      '#language' => $currentLang,
      '#theme' => 'avoindata_appfeed',
    );
  }
}
