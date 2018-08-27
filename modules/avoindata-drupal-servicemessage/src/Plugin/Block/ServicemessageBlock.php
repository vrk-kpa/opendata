<?php

namespace Drupal\avoindata_servicemessage\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;

/**
 * Provides a 'Avoindata Servicemessage' Block.
 *
 * @Block(
 *   id = "avoindata_servicemessage",
 *   admin_label = @Translation("Avoindata Servicemessage"),
 *   category = @Translation("Avoindata Servicemessage"),
 * )
 */
class ServicemessageBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();

    $messageNodeIdsQuery = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_servicemessage')
    ->condition('langcode', $lang);

    $messageNodeIds = $messageNodeIdsQuery
      ->execute();

    $messageNodes = \Drupal::entityTypeManager()
    ->getStorage('node')
    ->loadMultiple($messageNodeIds);

    $messages = [];

    foreach ($messageNodes as $key => $node) {
      array_push($messages, (object) array(
        'id' => $node->id(),
        'createdtime' => $node->getCreatedTime(),
        'body' => $node->body->getValue()[0]['value'],
        'severity' => $node->field_severity->getValue()[0]['value']
      ));
    }
    return array(
      '#theme' => 'avoindata_servicemessage',
      '#messages' => $messages,
      '#cache' => array(
        'tags' => ['node_list']
      )
    );
  }
}
