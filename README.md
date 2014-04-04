ytp-drupal-wysiwyg
==================

Drupal module that enables wysiwyg-editor automatically. Only automates wysiwyg installation.

Installation
------------

Requires Drupal and Drush.

    cd $DRUPAL_ROOT
    
    drush dl -y wysiwyg
    drush dl -y drush_editor
    drush en -y wysiwyg
    drush en -y drush_editor

    drush editor-download ckeditor

    git clone https://github.com/yhteentoimivuuspalvelut/ytp-drupal-wysiwyg.git $DRUPAL_ROOT/sites/all/modules/ytp_wysiwyg

    drush en -y ytp_wysiwyg
