<?php
/**
 * @file
 * feature_blocks_feature.features.fe_block_boxes.inc
 */

/**
 * Implements hook_default_fe_block_boxes().
 */
function feature_blocks_feature_default_fe_block_boxes() {
  $export = array();

  $fe_block_boxes = new stdClass();
  $fe_block_boxes->info = 'Front / Latest datasets';
  $fe_block_boxes->format = 'php_code';
  $fe_block_boxes->machine_name = 'latest_datasets';
  $fe_block_boxes->body = '            <?php
                $url = \'https://localhost/data/api/3/action/package_search?sort=metadata_created+desc&rows=5\';
                $options = array(
                    \'method\' => \'GET\'
                );

                $result = drupal_http_request($url, $options);
                $json = drupal_json_decode($result->data);
                $latest_datasets = $json["result"][\'results\'];

                global $language;
            ?>

            <ul class="dataset-title-list">
            <?php foreach ($latest_datasets as $dataset): ?>
                <li><i class="icon-book icon-2x"></i><a href="/data/<?php print $language->language ?>/dataset/<?php print $dataset[\'name\'] ?>"><?php print $dataset[\'title\'] ?></a></li>
            <?php endforeach ?>
            </ul>';

  $export['latest_datasets'] = $fe_block_boxes;

  $fe_block_boxes = new stdClass();
  $fe_block_boxes->info = 'Front / Most popular datasets';
  $fe_block_boxes->format = 'php_code';
  $fe_block_boxes->machine_name = 'popular_datasets';
  $fe_block_boxes->body = '           <?php
                $url = \'https://localhost/data/api/3/action/package_search?sort=views_recent+desc&rows=5\';
                $options = array(
                    \'method\' => \'GET\'
                );

                $result = drupal_http_request($url, $options);
                $json = drupal_json_decode($result->data);
                $latest_datasets = $json["result"][\'results\'];

                global $language;
            ?>

            <ul class="dataset-title-list">
            <?php foreach ($latest_datasets as $dataset): ?>
                <li><i class="icon-book icon-2x"></i><a href="/data/<?php print $language->language ?>/dataset/<?php print $dataset[\'name\'] ?>"><?php print $dataset[\'title\'] ?></a></li>
            <?php endforeach ?>
            </ul>';

  $export['popular_datasets'] = $fe_block_boxes;

  return $export;
}
