<?php

define('DRUPAL_ROOT', getcwd());

require_once DRUPAL_ROOT . '/includes/bootstrap.inc';
drupal_bootstrap(DRUPAL_BOOTSTRAP_FULL);

global $user;

user_cancel(array(), $user->uid, 'user_cancel_block_unpublish');

$batch =& batch_get();
$batch['progressive'] = FALSE;
batch_process();

drupal_goto("<front>");
