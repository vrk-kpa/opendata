<? php

namespace Drupal\avoindata_footer\Controller;

use Drupal\Core\Controller\ControllerBase;

class FooterController extends ControllerBase {
  public function footer() {
    $build = [
      '#markup' => t('Hello World!'),
    ];
    return $build;
  }
}
