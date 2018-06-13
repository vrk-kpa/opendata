<?php

namespace Drupal\avoindata_header\Controller;

use Drupal\Core\Controller\ControllerBase;
use \Symfony\Component\HttpFoundation\Response;

class HeaderController extends ControllerBase {
  public function header() {
    $build = array(
      '#theme' => 'avoindata_header'
    );
    // Only render this part, not the whole page
    return new Response(render($build));
  }
}
