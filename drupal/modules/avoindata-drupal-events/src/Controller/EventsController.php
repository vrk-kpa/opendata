<?php

namespace Drupal\avoindata_events\Controller;

use Drupal\datetime\Plugin\Field\FieldType\DateTimeItemInterface;
use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\Request;
use Drupal\Core\Datetime\DrupalDateTime;

/**
 * Adds event contoller.
 *
 * Class EventsController
 *   Implements event controller.
 *
 * @package Drupal\avoindata_events\Controller
 */
class EventsController extends ControllerBase {

  /**
   * Requests events from drupal.
   *
   * @param Symfony\Component\HttpFoundation\Request $request
   *   HTTP request.
   *
   * @return array
   *   Returns formatted array of events.
   */
  public function events(Request $request) {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    $currentDateTime = new DrupalDateTime('today');
    $currentDateTime->setTimezone(new \DateTimezone(DateTimeItemInterface::STORAGE_TIMEZONE));
    $formattedcurrentDateTime = $currentDateTime->format(DateTimeItemInterface::DATETIME_STORAGE_FORMAT);

    $sort = $request->query->get('sort') ?: 'asc';
    $searchterm = $request->query->get('search');
    $showpast = $request->query->get('past');

    $eventNodeIdsTitleQuery = \Drupal::entityQuery('node')
      ->condition('type', 'avoindata_event')
      ->condition('status', 1)
      ->condition('langcode', $lang);
    $eventNodeIdsBodyQuery = \Drupal::entityQuery('node')
      ->condition('type', 'avoindata_event')
      ->condition('status', 1)
      ->condition('langcode', $lang);

    if (!empty($searchterm)) {
      $eventNodeIdsTitleQuery = $eventNodeIdsTitleQuery
        ->condition('title', $searchterm, 'CONTAINS');
      $eventNodeIdsBodyQuery = $eventNodeIdsBodyQuery
        ->condition('body', $searchterm, 'CONTAINS');
    }

    if (empty($showpast) or (!empty($showpast) and strcmp($showpast, 'false') == 0)) {
      $emptyOrNotPastTitles = $eventNodeIdsTitleQuery
        ->orConditionGroup()
        ->notExists('field_end_date')
        ->condition('field_end_date', $formattedcurrentDateTime, '>=');
      $emptyOrNotPastBodies = $eventNodeIdsBodyQuery
        ->orConditionGroup()
        ->notExists('field_end_date')
        ->condition('field_end_date', $formattedcurrentDateTime, '>=');

      $eventNodeIdsTitleQuery = $eventNodeIdsTitleQuery->condition($emptyOrNotPastTitles);
      $eventNodeIdsBodyQuery = $eventNodeIdsBodyQuery->condition($emptyOrNotPastBodies);
    }

    $eventNodeIdsTitle = $eventNodeIdsTitleQuery
      ->execute();
    $eventNodeIdsBody = $eventNodeIdsBodyQuery
      ->execute();

    $eventNodeIdsCombined = array_unique(array_merge($eventNodeIdsTitle, $eventNodeIdsBody), SORT_REGULAR);

    $eventNodeIds = [];
    if (!empty($eventNodeIdsCombined)) {
      $eventNodeIdsQuery = \Drupal::entityQuery('node')
        ->condition('type', 'avoindata_event')
        ->condition('langcode', $lang)
        ->condition('nid', $eventNodeIdsCombined, 'IN');

      if (strcmp($sort, 'asc') == 0) {
        $eventNodeIds = $eventNodeIdsQuery
          ->sort('field_start_date', 'asc')
          ->execute();
        $sort = 'asc';
      }
      else {
        $eventNodeIds = $eventNodeIdsQuery
          ->sort('field_start_date', 'desc')
          ->execute();
        $sort = 'desc';
      }
    }

    $eventNodes = \Drupal::entityTypeManager()
      ->getStorage('node')
      ->loadMultiple($eventNodeIds);

    return [
      '#searchterm' => $searchterm,
      '#sort' => $sort,
      '#showpast' => $showpast,
      '#events' => $eventNodes,
      '#language' => $lang,
      '#theme' => 'avoindata_events',
      '#cache' => [
        'tags' => ['node_list'],
      ],
    ];
  }

}
