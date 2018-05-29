<?php

namespace Drupal\avoindata_newsfeed\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;
use Drupal\Core\Entity\Query\QueryFactory;

/**
 * Provides a 'Avoindata News Feed' Block.
 *
 * @Block(
 *   id = "avoindata_newsfeed",
 *   admin_label = @Translation("Avoindata News Feed"),
 *   category = @Translation("Avoindata News Feed"),
 * )
 */
class NewsFeedBlock extends BlockBase {

  /**
   * {@inheritdoc}
   */
  public function build() {
    $articleNodeIds = \Drupal::entityQuery('node')
    ->condition('type', 'article')
    ->sort('created' , 'DESC')
    ->range(0, 5)
    ->execute();
    $articleNodes = \Drupal::entityTypeManager()
    ->getStorage('node')
    ->loadMultiple($articleNodeIds);

    // TODO: How will we sort the upcoming events?
    $eventNodeIds = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_event')
    ->sort('created' , 'DESC')
    ->range(0, 5)
    ->execute();
    $eventNodes = \Drupal::entityTypeManager()
    ->getStorage('node')
    ->loadMultiple($eventNodeIds);

    return array(
      '#newsfeed' => $articleNodes,
      '#eventfeed' => $eventNodes,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_newsfeed',
    );
  }
}
