<?php

namespace Drupal\avoindata_header\Controller;

use Drupal\Core\Controller\ControllerBase;
use \Symfony\Component\HttpFoundation\Response;
use \Symfony\Component\HttpFoundation\RedirectResponse;

class HeaderController extends ControllerBase {
  public function header() {
    $build = array(
      '#theme' => 'avoindata_header'
    );
    // Only render this part, not the whole page
    return new Response(\Drupal::service('renderer')->renderRoot($build));
  }

  public function ckanprofile() {
    $accountName = \Drupal::currentUser()->getAccountName();
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    return new RedirectResponse('/data/' . $lang . '/user/' . $accountName);
  }
}
