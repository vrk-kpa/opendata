<?php

namespace Drupal\avoindata_newsfeed\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Component\Serialization\Json;
use Drupal\Core\Entity\Query\QueryFactory;
use Drupal\Core\Datetime\DrupalDateTime;

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
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    $currentDateTime = new DrupalDateTime('today');
    $currentDateTime->setTimezone(new \DateTimezone(DATETIME_STORAGE_TIMEZONE));
    $formattedcurrentDateTime = $currentDateTime->format(DATETIME_DATETIME_STORAGE_FORMAT);

    $articleNodeIds = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_article')
    ->condition('langcode', $lang)
    ->sort('created' , 'DESC')
    ->range(0, 5)
    ->execute();
    $articleNodes = \Drupal::entityTypeManager()
    ->getStorage('node')
    ->loadMultiple($articleNodeIds);

    $eventNodeIds = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_event')
    ->condition('langcode', $lang)
    ->condition('field_start_date', $formattedcurrentDateTime, '>=')
    ->sort('field_start_date' , 'ASC')
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
      '#cache' => array(
        'tags' => ['node_list']
      )
    );
  }
}
