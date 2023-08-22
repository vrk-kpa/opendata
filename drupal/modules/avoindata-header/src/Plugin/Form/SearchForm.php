<?php

namespace Drupal\avoindata_header\Plugin\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\Core\Url;

/**
 * Adds search form to header element.
 *
 * Class SearchForm
 *   Adds form.
 *
 * @package Drupal\avoindata_header\Plugin\Form
 */
class SearchForm extends FormBase {

  /**
   * {@inheritdoc}
   */
  public function getFormId() {
    return 'avoindata_search_id';
  }

  /**
   * {@inheritdoc}
   */
  public function buildForm(array $form, FormStateInterface $form_state) {
    // AV-2034: Set form action explicitly to drop query parameters reliably
    $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
    $form['#action'] = sprintf('/%s/api/header', $language);

    $form['searchfilter'] = [
      '#type' => 'textfield',
      '#default_value' => '1',
      '#attributes' => ['class' => ['input-header-search-filter', 'hidden']],
    ];

    $form['#theme'] = ['avoindata_search'];

    $form['search'] = [
      '#type' => 'textfield',
      '#default_value' => '',
    ];

    $form['actions']['submit'] = [
      '#type' => 'submit',
      '#value' => $this->t('Submit'),
      '#button_type' => 'primary',
    ];

    return $form;
  }

  /**
   * {@inheritdoc}
   */
  public function submitForm(array &$form, FormStateInterface $form_state) {
    $filter = $form_state->getValue('searchfilter');
    $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
    if ($language === 'en') {
      $language = 'en_GB';
    }
    $path = sprintf('/data/%s/search', $language);
    $url = url::fromUserInput($path, [
      'query' => ['q' => $form_state->getValue('search')]
    ]);
    $form_state->setRedirectUrl($url);
  }

}
