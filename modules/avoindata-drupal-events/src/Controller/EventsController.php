<?php

namespace Drupal\avoindata_events\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\Request;
use Drupal\Component\Serialization\Json;
use Drupal\Core\Entity\Query\QueryFactory;
use Drupal\taxonomy\Entity\Term;
use Drupal\Core\Datetime\DrupalDateTime;

class EventsController extends ControllerBase {
  public function events(Request $request) {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    $currentDateTime = new DrupalDateTime('today');
    $currentDateTime->setTimezone(new \DateTimezone(DATETIME_STORAGE_TIMEZONE));
    $formattedcurrentDateTime = $currentDateTime->format(DATETIME_DATETIME_STORAGE_FORMAT);

    $sort = $request->query->get('sort');
    $searchterm = $request->query->get('search');
    $showpast = $request->query->get('past');

    $eventNodeIdsTitleQuery = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_event')
    ->condition('langcode', $lang);
    $eventNodeIdsBodyQuery = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_event')
    ->condition('langcode', $lang);

    if(!empty($searchterm)) {
      $eventNodeIdsTitleQuery = $eventNodeIdsTitleQuery
      ->condition('title', $searchterm, 'CONTAINS');
      $eventNodeIdsBodyQuery = $eventNodeIdsBodyQuery
      ->condition('body', $searchterm, 'CONTAINS');
    }

    if(empty($showpast) OR (!empty($showpast) AND strcmp($showpast, 'false') == 0)) {
      $eventNodeIdsTitleQuery = $eventNodeIdsTitleQuery
      ->condition('field_start_date', $formattedcurrentDateTime, '>=');
      $eventNodeIdsBodyQuery = $eventNodeIdsBodyQuery
      ->condition('field_start_date', $formattedcurrentDateTime, '>=');
    }

    $eventNodeIdsTitle = $eventNodeIdsTitleQuery
    ->execute();
    $eventNodeIdsBody = $eventNodeIdsBodyQuery
    ->execute();

    $eventNodeIdsCombined = array_unique(array_merge($eventNodeIdsTitle,$eventNodeIdsBody), SORT_REGULAR);

    $eventNodeIds = array();
    if(!empty($eventNodeIdsCombined)) {
      $eventNodeIdsQuery = \Drupal::entityQuery('node')
      ->condition('type', 'avoindata_event')
      ->condition('langcode', $lang)
      ->condition('nid', $eventNodeIdsCombined, 'IN');
  
      if(strcmp($sort, 'asc') == 0) {
        $eventNodeIds = $eventNodeIdsQuery
        ->sort('field_start_date' , 'asc')
        ->execute();
        $sort = 'asc';
      } else {
        $eventNodeIds = $eventNodeIdsQuery
        ->sort('field_start_date' , 'desc')
        ->execute();
        $sort = 'desc';
      }
    }

    $eventNodes = \Drupal::entityTypeManager()
    ->getStorage('node')
    ->loadMultiple($eventNodeIds);


    return array(
      '#searchterm' => $searchterm,
      '#sort' => $sort,
      '#showpast' => $showpast,
      '#events' => $eventNodes,
      '#language' => $lang,
      '#theme' => 'avoindata_events',
      '#cache' => array(
        'tags' => ['node_list']
      )
    );
  }
}
