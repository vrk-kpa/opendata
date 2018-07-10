<?php

namespace Drupal\avoindata_articles\Controller;

use Drupal\Core\Controller\ControllerBase;
use \Symfony\Component\HttpFoundation\Response;

class ArticlesController extends ControllerBase {
  public function articles() {
    return array(
      '#theme' => 'avoindata_articles',
    );
  }
}
