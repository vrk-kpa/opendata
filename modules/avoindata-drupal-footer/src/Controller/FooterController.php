<?php

namespace Drupal\avoindata_footer\Controller;

use Drupal\Core\Controller\ControllerBase;
use \Symfony\Component\HttpFoundation\Response;

class FooterController extends ControllerBase {
  public function footer() {
    $build = array(
			'#theme' => 'avoindata_footer'
    );
    
		// Only render this part, not the whole page
    return new Response(\Drupal::service('renderer')->renderRoot($build));
  }
}
