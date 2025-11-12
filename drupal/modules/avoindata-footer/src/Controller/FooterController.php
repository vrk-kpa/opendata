<?php

namespace Drupal\avoindata_footer\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\Response;

/**
 * Adds controller for footer.
 *
 * Class FooterController
 *   Implements footer controller.
 *
 * @package Drupal\avoindata_footer\Controller
 */
class FooterController extends ControllerBase {

  /**
   * Builds footer response in api.
   *
   * @return Symfony\Component\HttpFoundation\Response
   *   Return html response of footer.
   */
  public function footer() {
    $build = [
      '#theme' => 'avoindata_footer',
    ];

    $response = new Response(\Drupal::service('renderer')->renderRoot($build));
    // Only render this part, not the whole page.
    return $response;
  }

}
