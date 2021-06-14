<?php

namespace Drupal\avoindata_header\Controller;

use Drupal\Core\Controller\ControllerBase;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\RedirectResponse;

/**
 * Adds support for header controller.
 *
 * Class HeaderController
 *    Builds header component in the api.
 *
 * @package Drupal\avoindata_header\Controller
 */
class HeaderController extends ControllerBase {

  /**
   * Build the header component.
   *
   * @return Symfony\Component\HttpFoundation\Response
   *   Return html response for the header.
   */
  public function header() {
    $build = [
      '#theme' => 'avoindata_header',
    ];
    $queryParams = \Drupal::request()->query->all();

    if (isset($queryParams['activePath'])) {
      \Drupal::service('path.current')->setPath($queryParams['activePath']);
    }

    $response = new Response(\Drupal::service('renderer')->renderRoot($build));
    $response->setCache(['public' => TRUE, 'max_age' => 3600]);
    // Only render this part, not the whole page.
    return $response;
  }

  /**
   * Creates html response for profile link.
   *
   * @return Symfony\Component\HttpFoundation\RedirectResponse
   *   Returns html response.
   */
  public function ckanprofile() {
    $accountName = \Drupal::currentUser()->getAccountName();
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    return new RedirectResponse('/data/' . $lang . '/user/' . $accountName);
  }

  /**
   * Creates html response for statistics link.
   *
   * @return Symfony\Component\HttpFoundation\RedirectResponse
   *   Returns html response.
   */
  public function ckanstatistics() {
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    return new RedirectResponse('/data/' . $lang . '/statistics');
  }

}
