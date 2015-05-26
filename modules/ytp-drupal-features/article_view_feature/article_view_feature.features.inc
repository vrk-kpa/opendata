<?php
/**
 * @file
 * article_view_feature.features.inc
 */

/**
 * Implements hook_views_api().
 */
function article_view_feature_views_api($module = NULL, $api = NULL) {
  return array("api" => "3.0");
}

function article_view_feature_theme($existing, $type, $theme, $path){
  return array (
    'views_view_unformatted__article_view' => array(
      'variables' => array('view' => NULL, 'options' => NULL, 'rows' => NULL, 'title' => NULL),
      'template' => 'views-view-unformatted--article-view',
      'base hook' => 'views-view-unformatted',
      'path' => drupal_get_path('module', 'article_view_feature') . '/templates/'
    ),
  );
}
