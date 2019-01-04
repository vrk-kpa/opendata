<?php

namespace Drupal\avoindata_header\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\Core\Render\HtmlResponse;
use \Symfony\Component\HttpFoundation\RedirectResponse;

class HeaderController extends ControllerBase {
  public function header() {
    $build = array(
      '#type' => 'html',
      'page' => [
        '#theme' => 'avoindata_header',
        '#attached' => array(
          'library' => array(
            'avoindata_header/avoindata_header',
          ),
        ),
      ],
    );
    // Only render this part, not the whole page
    $html = \Drupal::service('renderer')->renderRoot($build);
    $response = new HtmlResponse();
    $response->setContent($html);
    // Attach module related javascript
    $response->setAttachments($build['#attached']);
    return $response;
  }

  public function ckanprofile() {
    $accountName = \Drupal::currentUser()->getAccountName();
    $lang = \Drupal::languageManager()->getCurrentLanguage()->getId();
    return new RedirectResponse('/data/' . $lang . '/user/' . $accountName);
  }
}
