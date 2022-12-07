<?php

namespace Drupal\avoindata_articles\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\Request;
use Drupal\taxonomy\Entity\Term;

/**
 * Implements articles controller.
 */
class ArticlesController extends ControllerBase {

  /**
   * Queries articles from drupal.
   *
   * @param Symfony\Component\HttpFoundation\Request $request
   *   HTTP request.
   *
   * @return array
   *   Return array of articles.
   */
  public function articles(Request $request) {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();

    $searchterm = $request->query->get('search');
    $categoryfilter = $request->query->get('category');

    $articleNodeIdsTitleQuery = \Drupal::entityQuery('node')
      ->condition('type', 'avoindata_article')
      ->condition('langcode', $lang);
    $articleNodeIdsBodyQuery = \Drupal::entityQuery('node')
      ->condition('type', 'avoindata_article')
      ->condition('langcode', $lang);


    if (!empty($searchterm)) {
      $articleNodeIdsTitleQuery = $articleNodeIdsTitleQuery
        ->condition('title', $searchterm, 'CONTAINS');
      $articleNodeIdsBodyQuery = $articleNodeIdsBodyQuery
        ->condition('body', $searchterm, 'CONTAINS');
    }

    $articleNodeIdsTitle = $articleNodeIdsTitleQuery
      ->execute();
    $articleNodeIdsBody = $articleNodeIdsBodyQuery
      ->execute();

    $articleNodeIdsCombined = array_unique(array_merge($articleNodeIdsTitle, $articleNodeIdsBody), SORT_REGULAR);

    $articleNodeIds = [];
    if (!empty($articleNodeIdsCombined)) {
      $articleNodeIdsQuery = \Drupal::entityQuery('node')
        ->condition('type', 'avoindata_article')
        ->condition('langcode', $lang)
        ->condition('status', 1)
        ->condition('nid', $articleNodeIdsCombined, 'IN')
        ->sort('created', 'DESC');

      if (!empty($categoryfilter)) {
        foreach ($categoryfilter as &$categoryTagFilter) {
          $nodeTagAndQuery = $articleNodeIdsQuery->andConditionGroup();
          $nodeTagAndQuery->condition('field_tags', $categoryTagFilter);
          $articleNodeIdsQuery->condition($nodeTagAndQuery);
        }
      }

      $articleNodeIds = $articleNodeIdsQuery->execute();
    }

    $articleNodes = \Drupal::entityTypeManager()
      ->getStorage('node')
      ->loadMultiple($articleNodeIds);

    $articles = [];
    $taxonomyTermIds = [];
    $taxonomyTerms = [];

    foreach ($articleNodes as $key => $node) {
      $fieldTags = $node->get('field_tags')->getValue();
      $articleTags = [];
      if ($fieldTags) {
        foreach ($fieldTags as &$tag) {
          array_push($taxonomyTermIds, $tag['target_id']);
          array_push($articleTags, (object) [
            'tid' => $tag['target_id'],
            'name' => Term::load($tag['target_id'])->getName(),
          ]);
        }
      }
      array_push($articles, (object) [
        'id' => $node->id(),
        'label' => $node->label(),
        'createdtime' => $node->getCreatedTime(),
        'body' => $node->body->getValue(),
        'tags' => $articleTags,
      ]);
    }

    $taxonomyTermIds = array_unique($taxonomyTermIds);
    $taxonomyTerms = Term::loadMultiple($taxonomyTermIds);

    return [
      '#searchterm' => $searchterm,
      '#articles' => $articles,
      '#tags' => $taxonomyTerms,
      '#activetags' => $categoryfilter,
      '#language' => $lang,
      '#theme' => 'avoindata_articles',
      '#cache' => [
        'max-age' => 0,
        'tags' => ['node_list'],
      ],
    ];
  }

}
