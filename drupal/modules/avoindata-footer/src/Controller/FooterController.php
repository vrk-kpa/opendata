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
      '#site_logo' => avoindata_site_logo_path(),
    ];
    $render = \Drupal::service('renderer')->renderRoot($build);
    $response = new Response($render);
    // Only render this part, not the whole page.
    return $response;
  }

}

/**
 * Pick the correct logo
 *
 * @return string
 *   Return logo path
 */
function avoindata_site_logo_path() {

  $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
  $environment = theme_get_setting('environment');

  if ($environment == 'prod') {
    $logo = '/images/logo/logo_prod';
  }
  else {
    $logo = '/images/logo/logo_dev';
  }

  if ($language == 'fi' || $language == 'sv' || $language == 'en') {
    $logo = $logo . '_' . $language;
  }

  $theme_path = \Drupal::theme()->getActiveTheme()->getPath();
  return base_path() . $theme_path . $logo . '.svg';
}
