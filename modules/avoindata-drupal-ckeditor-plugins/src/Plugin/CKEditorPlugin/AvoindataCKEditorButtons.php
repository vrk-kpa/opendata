<?php

namespace Drupal\avoindata_ckeditor_plugins\Plugin\CKEditorPlugin;

use Drupal\ckeditor\CKEditorPluginBase;
use Drupal\editor\Entity\Editor;

/**
 * Defines the buttons for avoindata ckeditor.
 *
 * @CKEditorPlugin(
 *   id = "avoindata_ckeditor_buttons",
 *   label = @Translation("Avoindata CKEditor buttons")
 * )
 */
class AvoindataCKEditorButtons extends CKEditorPluginBase {

  /**
   * {@inheritdoc}
   *
   * NOTE: The keys of the returned array corresponds to the CKEditor button
   * names. They are the first argument of the editor.ui.addButton() or
   * editor.ui.addRichCombo() functions in the plugin.js file.
   */
  public function getButtons() {
    // Make sure that the path to the image matches the file structure of
    // the CKEditor plugin you are implementing.
    $path = drupal_get_path('module', 'avoindata_ckeditor_plugins') . '/icons';
    return [
      'avoindata_example' => [
        'label' => $this->t('Avoindata example'),
        'image' => $path . '/avoindata_example.png',
      ],
      'avoindata_expander' => [
        'label' => $this->t('Avoindata expander'),
        'image' => $path . '/avoindata_expander.png',
      ],
      'avoindata_external-link' => [
        'label' => $this->t('Avoindata external-link'),
        'image' => $path . '/avoindata_external-link.svg',
      ],
      'avoindata_hint' => [
        'label' => $this->t('Avoindata hint'),
        'image' => $path . '/avoindata_hint.png',
      ],
      'avoindata_note' => [
        'label' => $this->t('Avoindata note'),
        'image' => $path . '/avoindata_note.png',
      ],
      'avoindata_section' => [
        'label' => $this->t('Avoindata section'),
        'image' => $path . '/avoindata_section.png',
      ],
    ];
  }

  /**
   * {@inheritdoc}
   */
  public function getFile() {
    // Make sure that the path to the plugin.js matches the file structure of
    // the CKEditor plugin you are implementing.
    return drupal_get_path('module', 'avoindata_ckeditor_plugins') . '/js/plugin.js';
  }

  /**
   * {@inheritdoc}
   */
  public function isInternal() {
    return FALSE;
  }

  /**
   * {@inheritdoc}
   */
  public function getDependencies(Editor $editor) {
    return [];
  }

  /**
   * {@inheritdoc}
   */
  public function getLibraries(Editor $editor) {
    return [];
  }

  /**
   * {@inheritdoc}
   */
  public function getConfig(Editor $editor) {
    return [];
  }

}
