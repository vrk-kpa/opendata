 <script type="text/javascript">
    jQuery(document).ready(function(){
        jQuery("input[name$='searchtype']").parent().click(function() {
            var searchType = jQuery(this).find('input').val();
            jQuery("div.navbar-search").hide();
            jQuery("#search_" + searchType).show();
            jQuery("label.btn-primary").removeClass("btn-primary").addClass("btn-default");
            jQuery(this).removeClass("btn-default").addClass("btn-primary");
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
?>
<div id="search-box">

    <div id="search_datasets" class="navbar navbar-search form-control" role="search">
       <form class="navbar-form" action="/data/<?php print $language->language ?>/dataset">
            <input class="search-term" type="text" name="q" placeholder="<?php print t("Search datasets...")?>">
            <button type="submit" class="search-submit" value="<?php t("Search")?>" ><i class="fa fa-search"></i><span><?php print t("Search")?></span></button>
            <input type="hidden" name="sort" value="score desc, metadata_modified desc" />
        </form>
    </div>
    <div id="search_content" class="navbar navbar-search form-control" role="search" style="display: none;">
         <?php
              if (isset($search_box)) {
                print $search_box;
              }
         ?>
    </div>
    <div class="btn-group btn-group-sm" data-toggle="buttons">
        <label class="btn btn-primary active"><input type="radio" name="searchtype" checked="checked" value="datasets"/><?php print t("From datasets")?></label>
        <label class="btn btn-default"><input type="radio" name="searchtype" value="content"/><?php print t("From other content")?></label>
    </div>
    <div class="collection-links">
        <h3><a href="/data/<?php print $language->language ?>/dataset?collection_type=Open+Data"><?php print t("Open Data")?> &gt;</a></h3>
        <h3><a href="/data/<?php print $language->language ?>/dataset?collection_type=Interoperability+Tools"><?php print t("Interoperability Tools")?> &gt;</a></h3>
    </div>
  </div>

