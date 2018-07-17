<?php

namespace Drupal\avoindata_articles\Controller;

use Drupal\Core\Controller\ControllerBase;
use \Symfony\Component\HttpFoundation\Response;
use Drupal\Component\Serialization\Json;
use Drupal\Core\Entity\Query\QueryFactory;
use Drupal\taxonomy\Entity\Term;

class ArticlesController extends ControllerBase {
  public function articles() {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();

    $articleNodeIds = \Drupal::entityQuery('node')
    ->condition('type', 'article')
    ->condition('langcode', $lang)
    ->sort('created' , 'DESC')
    ->execute();
    $articleNodes = \Drupal::entityTypeManager()
    ->getStorage('node')
    ->loadMultiple($articleNodeIds);

    $articles = [];
    $taxonomyTermIds = [];
    $taxonomyTerms = [];

    foreach ($articleNodes as $key => $node) {
      $fieldTags = $node->get('field_tags')->getValue();
      $articleTags = [];
      if($fieldTags) {
        foreach($fieldTags as &$tag) {
          array_push($taxonomyTermIds, $tag['target_id']);
          array_push($articleTags, (object) array(
             'tid' => $tag['target_id'],
             'name' => Term::load($tag['target_id'])->getName()
          ));
        }
      }
      array_push($articles, (object) array(
        'id' => $node->id(),
        'label' => $node->label(),
        'createdtime' => $node->getCreatedTime(),
        'body' => $node->body->getValue(),
        'tags' => $articleTags
      ));
    }

    $taxonomyTermIds = array_unique($taxonomyTermIds);
    $taxonomyTerms = Term::loadMultiple($taxonomyTermIds);


    return array(
      '#articles' => $articles,
      '#tags' => $taxonomyTerms,
      '#language' => $lang,
      '#theme' => 'avoindata_articles',
    );
  }
}
