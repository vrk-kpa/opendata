 <script type="text/javascript">
    jQuery(document).ready(function(){
        jQuery("input[name$='searchtype']").click(function() {
            var searchType = jQuery(this).val();
            jQuery("div.navbar-search").hide();
            jQuery("#search_" + searchType).show();
         });
    });
</script>
<style>
label{
     font-size:10px;
     vertical-align: middle;
    }
    input[type="radio"]{
     float:left;
    }
</style>
<?php
    global $language;

/*
 *  Preprocess block-hader.tpl.php to inject the $search_box variable back into D7.
 */
function MYTHEME_preprocess_page(&$variables){
  $search_box = drupal_render(drupal_get_form('search_form'));
  $variables['search_box'] = $search_box;
}
?>
<div id="search-box">
    <div class="filtering">
        <label><input type="radio" name="searchtype" checked="checked" value="1"/><?php print t("Search datasets")?></label>
        <label><input type="radio" name="searchtype" value="2"/><?php print t("Global search")?></label>
    </div>
     <h1><?php print t('Search') ?></h1>
    <div id="search_1" class="navbar navbar-search form-control" role="search">
       <form class="navbar-form" action="/data/<?php print $language->language ?>/dataset">
            <input class="search-term" type="text" name="q" placeholder="<?php print t("Search datasets...")?>">
            <button type="submit" class="search-submit" value="<?php t("Search")?>" ><i class="icon-search"></i><span><?php print t("Search")?></span></button>
            <input type="hidden" name="sort" value="score desc, metadata_modified desc" />
        </form>
    </div>
    <div id="search_2" class="navbar navbar-search form-control" role="search" style="display: none;">
         <?php
             print $search_box; 
         ?>
    </div>
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

