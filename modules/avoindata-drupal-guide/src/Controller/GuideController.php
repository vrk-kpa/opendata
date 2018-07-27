<?php

namespace Drupal\avoindata_guide\Controller;

use Drupal\Core\Controller\ControllerBase;

class GuideController extends ControllerBase {
  public function guide($guidePageTitle) {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    $guidePageTitleQuery = \Drupal::entityQuery('node')
    ->condition('type', 'avoindata_guide_page')
    ->condition('title', $guidePageTitle);

    $guidePage = $guidePageTitleQuery->execute();
    $allPages = \Drupal::entityQuery('node')->condition('type', 'avoindata_guide_page')->execute();
    return array(
      '#language' => $lang,
      '#guidePageTitle' => $guidePageTitle,
      '#guidePage' => $guidePage,
      '#allPages' => $allPages,
      '#theme' => 'avoindata_guide'
    );
  }
}
