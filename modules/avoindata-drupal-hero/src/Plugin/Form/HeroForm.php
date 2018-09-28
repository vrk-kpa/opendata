<?php
/**
 * @file
 */
namespace Drupal\avoindata_hero\Plugin\Form;
use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\Core\Url;
use Drupal\Component\Serialization\Json;

class HeroForm extends FormBase {

  /**
   * {@inheritdoc}
   */
  public function getFormId() {
    return 'avoindata_hero_id';
  }

  /**
   * {@inheritdoc}
   */
  public function buildForm(array $form, FormStateInterface $form_state) {
    $client = \Drupal::httpClient();

    try {
      $datasetResponse = $client->request('GET', 'http://localhost:8080/data/api/3/action/package_search');
      $datasetResult = Json::decode($datasetResponse->getBody());
      $datasetCount = $datasetResult['result']['count'];
    } catch (\Exception $e) {
      $datasetCount = 0;
    }

    try {
      $organizationResponse = $client->request('GET', 'http://localhost:8080/data/api/3/action/organization_list');
      $organizationResult = Json::decode($organizationResponse->getBody());
      $organizationCount = count($organizationResult['result']);
    } catch (\Exception $e) {
      $organizationCount = 0;
    }

    try {
      $applicationResponse = $client->request('GET', 'http://localhost:8080/data/api/3/action/ckanext_showcase_list');
      $applicationResult = Json::decode($applicationResponse->getBody());
      $applicationCount = count($applicationResult['result']);
    } catch (\Exception $e) {
      $applicationCount = 0;
    }

    $form['datasetcount'] = array(
      '#markup' => $datasetCount,
    );

    $form['organizationcount'] = array(
      '#markup' => $organizationCount,
    );

    $form['applicationcount'] = array(
      '#markup' => $applicationCount,
    );

    $form['searchfilter'] = array(
      '#type' => 'textfield',
      '#default_value' => '1',
      '#attributes' => array('class' => array('input-hero-search-filter', 'hidden')),
    );

    $form['search'] = array(
      '#type' => 'textfield',
      '#attributes' => array('class' => array('input-hero-search')),
    );

    $form['actions']['submit'] = array(
      '#type' => 'submit',
      // Unicode used to avoid "Theme Button Iconization for search keyword
      '#value' => $this->t('<i class="fas">&#xf002;</i>'),
      '#attributes' => array('class' => array('btn-hero-search')),
    );

    $form['#theme'] = ['avoindata_hero'];

    return $form;
  }

  /**
   * {@inheritdoc}
   */
  public function validateForm(array &$form, FormStateInterface $form_state) {
    if (strlen($form_state->getValue('search')) < 2) {
      $form_state->setErrorByName('search', $this->t('Query must be at least three characters long'));
    }
  }

  /**
   * {@inheritdoc}
   */
  public function submitForm(array &$form, FormStateInterface $form_state) {
    $filter = $form_state->getValue('searchfilter');
    $base_path = '/data/fi/dataset?q=%s';

    if($filter == '2') {
      $base_path = '/data/fi/showcase?q=%s';
    } elseif ($filter == '3') {
      $base_path = '/data/fi/organization?q=%s';
    }

    $redirect_path = sprintf($base_path, $form_state->getValue('search'));
    $url = url::fromUserInput($redirect_path);
    $form_state->setRedirectUrl($url);
  }
}
