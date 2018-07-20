<?php

namespace Drupal\avoindata_events\Controller;

use Drupal\Core\Controller\ControllerBase;
use \Symfony\Component\HttpFoundation\Response;
use Drupal\Component\Serialization\Json;
use Drupal\Core\Entity\Query\QueryFactory;
use Drupal\taxonomy\Entity\Term;

class EventsController extends ControllerBase {
  public function events($sort, $searchterm) {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();

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
      '#events' => $eventNodes,
      '#language' => $lang,
      '#theme' => 'avoindata_events',
    );
  }
}
