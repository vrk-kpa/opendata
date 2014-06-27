    <?php

    ?>

    <!--
        Top navbar
    -->
    <div class="navbar navbar-inverse navbar-fixed-top" role="navigation">
      <div class="container">
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
              $logos = array(
                      "avoindata.fi" => "avoindata_fi.png",
                      "www.avoindata.fi" => "avoindata_fi.png",
                      "alpha.avoindata.fi" => "avoindata_fi_alpha.png",
                      "beta.avoindata.fi" => "avoindata_fi_beta.png",

                      "opendata.fi" => "opendata_fi.png",
                      "www.opendata.fi" => "opendata_fi.png",
                      "alpha.opendata.fi" => "opendata_fi_alpha.png",
                      "beta.opendata.fi" => "opendata_fi_beta.png",
              );
              $logo = isset($logos[$_SERVER['HTTP_HOST']]) ? $logos[$_SERVER['HTTP_HOST']] : 'opendata_fi_alpha.png';
              echo '<img src="/resources/images/logo/' . $logo . '" class="site-logo" />';
              ?>
          </a>
        </div>
        <div id="navbar-top-collapse" class="collapse navbar-collapse">

          <div class="visible-xs visible-sm visible-md">
              <ul class="nav navbar-nav user-nav navbar-right">
                   <?php buildMainNavBar(false); ?>
                   <?php if (user_is_logged_in()) { ?>
                   <li><a href="<?php print url('user') ?>"> <?php print t('User Info') ?></a></li>
                   <?php } ?>
                   <?php print render($page['top_navigation']); ?>
              </ul>
          </div>
          <div class="hidden-xs hidden-sm hidden-md">
          <?php print render($page['top_navigation']); ?>

          <ul class="nav navbar-nav user-nav navbar-right ">
            <li>
                <?php if (!user_is_logged_in()) { ?>
                <a href="/<?php echo $language->language; ?>/user/login" class="login"><?php echo t("Log in"); ?> &gt;</a></li>
                <?php } else { ?>
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
                | <a href="/<?php echo $language->language; ?>/user/logout" class="login"><?php echo t("Log out"); ?> &gt;</a></li>
                <?php } ?>
            <li><a href="#"><span class="icon icon-cart-navbar"></span> <?php echo t("Own checklist"); ?> (0)</a></li>
          </ul>

          </div>
        </div><!--/.nav-collapse -->
      </div>
    </div>

    <!--
      Main menu navbar
    -->
    <div class="container hidden-xs hidden-sm hidden-md">
      <nav class="navbar navbar-main" role="main-navigation">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#main-navigation-collapse">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand visible-xs" href="#">Päävalikko</a>
        </div>

        <!-- Collect the nav links, forms, and other content for toggling -->
        <div id="main-navigation-collapse" class="collapse navbar-collapse">
          <ul class="nav navbar-nav" id="main-navigation-links">
            <?php
            function buildMainNavBar($useActiveHiLight){

                global $language;
                global $site_section;

                $uri = $_SERVER['REQUEST_URI'];
                $lang = $language->language;

                $class = '';
                $href = '/' . $lang;
                if ( ($uri == $href || $site_section == t("Home") || $uri == '' || $uri == '/') && $useActiveHiLight == true) { $class = ' class="active" '; }
                echo '<li' . $class . '><a href='. $href . '>' . t("Home") . '</a></li>';

                $class = '';
                $href = '/data/' . $lang . '/dataset';
                if ( ($uri ==  $href || $site_section == t("Data Repositories")) && $useActiveHiLight == true) { $class = ' class="active" '; }
                echo '<li' . $class . '><a href="' . $href . '">' . t("Data Repositories") . '</a></li>';

                $class = '';
                $href = '/data/' . $lang . '/organization';
                if ( ($uri ==  $href || $site_section == t("Data Producers")) && $useActiveHiLight == true) { $class = ' class="active" '; }
                echo '<li' . $class . '><a href="' . $href . '">' . t("Data Producers") . '</a></li>';

                $class = '';
                // Link to different pages depending on if the user is logged in or not
                if (user_is_logged_in()) {
                    $href = '/data/' . $lang . '/dataset/new';
                } else {
                    $href = '/' . $lang . '/publish';
                }
                if ( ($uri == $href || $site_section == t("Publish Data")) && $useActiveHiLight == true) { $class = ' class="active" '; }
                echo '<li' . $class . '><a href='. $href . '>' . t("Publish Data") . '</a></li>';

                $class = '';
                $href = '/' . $lang . '/news';
                if ( ($uri == $href || $site_section == t("News")) && $useActiveHiLight == true) { $class = ' class="active" '; }
                echo '<li' . $class . '><a href='. $href . '>' . t("News") . '</a></li>';

                $class = '';
                $href = '/' . $lang . '/about';
                if ( ($uri == $href || $site_section == t("About us")) && $useActiveHiLight == true) { $class = ' class="active" '; }
                echo '<li' . $class . '><a href='. $href . '>' . t("About us") . '</a></li>';

            }

            buildMainNavBar(true);
            ?>

          </ul>
        </div><!-- /.navbar-collapse -->
      </nav>
    </div><!-- /.container -->

