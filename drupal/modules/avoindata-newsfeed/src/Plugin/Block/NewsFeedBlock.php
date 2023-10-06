<?php

namespace Drupal\avoindata_newsfeed\Plugin\Block;

use Drupal\Core\Block\BlockBase;
use Drupal\Core\Datetime\DrupalDateTime;
use Drupal\datetime\Plugin\Field\FieldType\DateTimeItemInterface;
use Drupal\taxonomy\Entity\Term;

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
    $currentDateTime->setTimezone(new \DateTimezone(DateTimeItemInterface::STORAGE_TIMEZONE));
    $formattedcurrentDateTime = $currentDateTime->format(DateTimeItemInterface::DATETIME_STORAGE_FORMAT);

    $articleNodeIds = \Drupal::entityQuery('node')
      ->condition('type', 'avoindata_article')
      ->condition('langcode', $lang)
      ->condition('status', 1)
      ->sort('created', 'DESC')
      ->range(0, 4)
      ->execute();
    $articleNodes = \Drupal::entityTypeManager()
      ->getStorage('node')
      ->loadMultiple($articleNodeIds);

    $eventNodeIds = \Drupal::entityQuery('node')
      ->condition('type', 'avoindata_event')
      ->condition('langcode', $lang)
      ->condition('field_start_date', $formattedcurrentDateTime, '>=')
      ->sort('field_start_date', 'ASC')
      ->range(0, 4)
      ->execute();
    $eventNodes = \Drupal::entityTypeManager()
      ->getStorage('node')
      ->loadMultiple($eventNodeIds);

    $articles = [];
    foreach ($articleNodes as $key => $node) {
      $fieldTags = $node->get('field_tags')->getValue();
      $articleTags = [];
      if ($fieldTags) {
        foreach ($fieldTags as &$tag) {
          array_push(
                $articleTags, (object) [
                  'tid' => $tag['target_id'],
                  'name' => Term::load($tag['target_id'])->getName(),
                ]
            );
        }
      }

      array_push(
            $articles, (object) [
              'id' => $node->id(),
              'label' => $node->label(),
              'createdtime' => $node->getCreatedTime(),
              'body' => $node->body->getValue(),
              'tags' => $articleTags,
            ]
        );
    }

    return [
      '#articles' => $articles,
      '#newsfeed' => $articleNodes,
      '#eventfeed' => $eventNodes,
      '#language' => \Drupal::languageManager()->getCurrentLanguage()->getId(),
      '#theme' => 'avoindata_newsfeed',
      '#cache' => [
        'tags' => ['node_list'],
      ],
    ];
  }

}
