<?php

?>
<!--
  Main menu navbar
-->
<div class="container-fluid hidden-xs">
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
        buildMainNavBar(true);
        ?>
      </ul>
    </div><!-- /.navbar-collapse -->
  </nav>
</div><!-- /.container -->

