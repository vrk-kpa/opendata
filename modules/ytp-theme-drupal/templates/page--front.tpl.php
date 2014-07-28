<?php


$ytp_custom_top = '<div class="navbar navbar-search form-control" role="search">' .
                  '  <form class="navbar-form" action="/data/' . $language->language . '/dataset">' .
                  '    <input class="search-term" type="text" name="q" placeholder="' . t("Search datasets...") . '">' .
                  '    <button type="submit" class="search-submit" value="' . t("Search") . '" ><i class="icon-search"></i><span>' . t("Search") .'</span>'  .
                  '    <input type="hidden" name="sort" value="score desc, metadata_modified desc" />' .
                  '  </form>' .
                  '</div>';

include("include/page.php");

