<?php
  function buildMainNavBar($useActiveHiLight){
    global $language;
    global $site_section;
    global $user;

    $uri = $_SERVER['REQUEST_URI'];
    $lang = $language->language;

    $class = '';
    $href = '/' . $lang;
    if ( ($uri == $href || $site_section == t("Home") || $uri == '' || $uri == '/') && $useActiveHiLight == true) { $class = ' class="active" '; }
    echo '<li' . $class . '><a href='. $href . '>' . t("Home") . '</a></li>';

    $class = '';
    $href = '/data/' . $lang . '/dataset';
    if ( ($uri ==  $href || $site_section == t("Datasets")) && $useActiveHiLight == true) { $class = ' class="active" '; }
    echo '<li' . $class . '><a href="' . $href . '">' . t("Datasets") . '</a></li>';

    $class = '';
    $href = '/data/' . $lang . '/organization';
    if ( ($uri ==  $href || $site_section == t("Organizations")) && $useActiveHiLight == true) { $class = ' class="active" '; }
    echo '<li' . $class . '><a href="' . $href . '">' . t("Organizations") . '</a></li>';

    $class = '';
    $href = '/' . $lang . '/publish';
    if ( ($uri == $href || $site_section == t("Publish Datasets")) && $useActiveHiLight == true) { $class = ' class="active" '; }
    echo '<li' . $class . '><a href='. $href . '>' . t("Publish Datasets") . '</a></li>';


    $class = '';
    $href = '/' . $lang . '/training';
    if ( ($uri == $href || $site_section == t("Training")) && $useActiveHiLight == true) { $class = ' class="active" '; }
    echo '<li' . $class . '><a href='. $href . '>' . t("Training") . '</a></li>';


    $class = '';
    $href = '/' . $lang . '/about';
    if ( ($uri == $href || $site_section == t("About us")) && $useActiveHiLight == true) { $class = ' class="active" '; }
    echo '<li' . $class . '><a href='. $href . '>' . t("About us") . '</a></li>';

    $class = '';
    $href = '/' . $lang . '/feedback';
    if ( ($uri == $href || $site_section == t("Feedback")) && $useActiveHiLight == true) { $class = ' class="active" '; }
    echo '<li' . $class . '><a href='. $href . '>' . t("Feedback") . '</a></li>';
  }
?>

<!--
    Top navbar
-->
<div class="navbar navbar-inverse navbar-top" role="navigation">
  <div class="container-fluid">
    <div class="navbar-header">
      <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navbar-top-collapse">
        <span class="sr-only">Toggle navigation</span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="navbar-brand" href="/<?php echo $language->language; ?>">
          <?php
          // We want to get default domain or domain with last two items in it: example.com instead www.example.com.
          // Checking if host is ip using numeric start is not perfect but fast and good enough for our purposes. 
          $domain = null;

          /*
          $logos = array(
                  "avoindata.fi" => "avoindata_fi.png",
                  "www.avoindata.fi" => "avoindata_fi.png",
                  "alpha.avoindata.fi" => "avoindata_fi.png",
                  "beta.avoindata.fi" => "avoindata_fi.png",

                  "opendata.fi" => "opendata_fi.png",
                  "www.opendata.fi" => "opendata_fi.png",
                  "alpha.opendata.fi" => "opendata_fi.png",
                  "beta.opendata.fi" => "opendata_fi.png",
          );

          $logo = isset($logos[$_SERVER['HTTP_HOST']]) ? $logos[$_SERVER['HTTP_HOST']] : 'opendata_fi.png';
          echo '<img src="/resources/images/logo/' . $logo . '" class="site-logo" />';
          */

          $current_lang = $language->language;
          $host = isset($_SERVER['HTTP_HOST']) ? $_SERVER['HTTP_HOST'] : 'avoindata.fi';

          $logos_avoindata = array(
              "fi" => "avoindata_fi.png",
              "en" => "avoindata_en.png",
              "sv" => "avoindata_se.png",
          );

          $logos_opendata = array(
              "fi" => "opendata_fi.png",
              "en" => "opendata_en.png",
              "sv" => "opendata_se.png",
          );

          // show a different logo depending on the domain and language used.
          if (strpos($host,'avoindata') !== false) {
            $logo_lang = isset($logos_avoindata[$current_lang]) ? $logos_avoindata[$current_lang] : 'avoindata_fi.png';
          } elseif (strpos($host,'opendata') !== false) {
            $logo_lang = isset($logos_opendata[$current_lang]) ? $logos_opendata[$current_lang] : 'opendata_en.png';
          }

          echo '<img src="/resources/images/logo/' . $logo_lang . '" class="site-logo" />';

          ?>
      </a>
    </div>

    <div id="navbar-top-collapse" class="collapse navbar-collapse">
      <div class="visible-xs visible-sm">
          <ul class="nav navbar-nav user-nav">
               <?php buildMainNavBar(false); ?>
               <?php if (user_is_logged_in()) { ?>
               <li><a href="<?php print url('user') ?>"> <?php print t('User Info') ?></a></li>
               <li><a href="<?php print url('user/logout') ?>"> <?php print t('Log out') ?></a></li>;
               <?php } ?>
               <?php print render($page['top_navigation']); ?>
          </ul>
      </div>
      <div class="hidden-xs hidden-sm">
          <?php
            $temp = user_load($user->uid);
            $new_activities = 0;
            if ( isset($temp->field_ckan_api_key['und']) && isset($temp->field_ckan_api_key['und'][0]) && isset($temp->field_ckan_api_key['und'][0]['value'])){
              $url = 'https://localhost/data/api/3/action/dashboard_new_activities_count';
              $options = array(
                'method' => 'GET',
                'headers' => array('Authorization' => $temp->field_ckan_api_key['und'][0]['value'])
              );
              $result = drupal_http_request($url, $options);
              $json = drupal_json_decode($result->data);
              $new_activities = $json["result"];
            }
        ?>

        <?php print render($page['top_navigation']); ?>
        <ul class="nav navbar-nav user-nav navbar-right user-nav-large">
          <?php if (!user_is_logged_in()) { ?>
          <li class="user-login">
            <a href="/<?php echo $language->language; ?>/user/login" class="login"><?php echo t("Log in"); ?></a>
          </li>

          <?php } else { ?>
          <li class="user-info">
            <a href="/data/<?php echo $language->language; ?>/user/<?php global $user; print_r($user->name);?>">
              <?php
              global $user; $temp =  user_load($user->uid);
              if (isset($temp->field_fullname['und'])) {
                  if (isset($temp->field_fullname['und'][0]) ) {
                      if (isset($temp->field_fullname['und'][0]['value'])) {
                           $fullname=$temp->field_fullname['und'][0]['value'];
                      }
                  }
              }
              if (isset($fullname)) { print_r($fullname);}else{ print_r($user->name);} 
              ?>
            </a>
          </li>
          <li class="notifications">
               <a href="/data/<?php echo $language->language; ?>/dashboard">
                  <i class="icon-dashboard"></i>
                  <span><?php echo $new_activities; ?></span>
               </a>
          </li>
          <li>
            <a href="/<?php echo $language->language; ?>/user/logout" class="login"><?php echo t("Log out"); ?></a>
          </li>
          <?php } ?>
          <!-- <li><a href="#"><span class="icon icon-cart-navbar"></span> <?php echo t("Own checklist"); ?> (0)</a></li> -->
        </ul>
      </div>
    </div><!--/.nav-collapse -->
  </div>
</div>
