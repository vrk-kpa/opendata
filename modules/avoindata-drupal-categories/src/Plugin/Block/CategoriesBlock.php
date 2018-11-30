<?php

namespace Drupal\avoindata_categories\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;

/**
 * Provides a 'Avoindata Categories' Block.
 *
 * @Block(
 *   id = "avoindata_categories",
 *   admin_label = @Translation("Avoindata Categories"),
 *   category = @Translation("Avoindata Categories"),
 * )
 */
class CategoriesBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    $client = \Drupal::httpClient();

    try {
      $response = $client->request('GET', 'http://localhost:8080/data/api/3/action/group_list?all_fields=true&include_extras=true');
      $result = Json::decode($response->getBody());
      $categories = $result['result'];
    } catch (\Exception $e) {
      $categories = NULL;
    }
    
    return array(
      '#theme' => 'avoindata_categories',
      '#categories' => $categories,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
    );
  }
}
