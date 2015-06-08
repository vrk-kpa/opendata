<?php
    global $language;
?>
<div id="search-box">
    <h1><?php print t('Search') ?></h1>
    <div class="navbar navbar-search form-control" role="search">
        <form class="navbar-form" action="/data/<?php print $language->language ?>/dataset">
            <input class="search-term" type="text" name="q" placeholder="<?php print t("Search datasets...")?>">
            <button type="submit" class="search-submit" value="<?php t("Search")?>" ><i class="icon-search"></i><span><?php print t("Search")?></span></button>
            <input type="hidden" name="sort" value="score desc, metadata_modified desc" />
        </form>
    </div>
    <div class="info">
        <h3><a href="/data/<?php print $language->language ?>/dataset?collection_type=Open+Data"><?php print t("Open Data datasets")?></a></h3>
        <h3><a href="/data/<?php print $language->language ?>/dataset?collection_type=Interoperability+Tools"><?php print t("Interoperability Tools")?></a></h3>
        <?php
            $url = 'https://localhost/data/api/3/action/package_search';
            $options = array(
              'method' => 'GET'
            );
            $result = drupal_http_request($url, $options);
            $json = drupal_json_decode($result->data);
            $dataset_count = $json["result"]['count'];



        ?>
        <div class="info-footer">
            <?php print t('Currently service has @dataset_count datasets.', array('@dataset_count' => $dataset_count)) ?>
        </div>

    </div>
</div>
