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

    $eventNodeIdsQuery = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_event')
    ->condition('langcode', $lang);

    if(!empty($searchterm)) {
      $eventNodeIdsQuery = $eventNodeIdsQuery
      ->condition('title', $searchterm, 'CONTAINS');
    }

    $eventNodeIds = NULL;
    if(strcmp($sort, 'asc') == 0) {
      $eventNodeIds = $eventNodeIdsQuery
      ->sort('created' , 'asc')
      ->execute();
      $sort = 'asc';
    } else {
      $eventNodeIds = $eventNodeIdsQuery
      ->sort('created' , 'desc')
      ->execute();
      $sort = 'desc';
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
