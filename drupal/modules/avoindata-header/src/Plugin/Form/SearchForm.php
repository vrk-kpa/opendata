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
    $form['language'] = \Drupal::languageManager()->getCurrentLanguage()->getId();

    $form['searchfilter'] = [
      '#type' => 'textfield',
      '#default_value' => '1',
      '#attributes' => ['class' => ['input-header-search-filter', 'hidden']],
    ];

    $form['#theme'] = ['avoindata_search'];

    $form['#language'] = \Drupal::languageManager()->getCurrentLanguage()->getId();

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
  public function validateForm(array &$form, FormStateInterface $form_state) {
    // Commented out for now as this breaks using the searchbar on the /search page if user 
    // submits less than 3 characters.
  }

  /**
   * {@inheritdoc}
   */
  public function submitForm(array &$form, FormStateInterface $form_state) {
    $filter = $form_state->getValue('searchfilter');
    $language = \Drupal::languageManager()->getCurrentLanguage()->getId();
    $base_path = '/data/%s';

    if ($language === 'en') {
      $base_path = sprintf($base_path, 'en_GB');
    }
    else {
      $base_path = sprintf($base_path, $language);
    }

    $base_path = $base_path . '/search';
    $base_path = $base_path . '?q=%s';
    $redirect_path = sprintf($base_path, $form_state->getValue('search'));
    $url = url::fromUserInput($redirect_path);
    $form_state->setRedirectUrl($url);
  }

}
