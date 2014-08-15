<?php
/**
 * @file
 * Default theme implementation to display a single Drupal page.
 *
 * The doctype, html, head and body tags are not in this template. Instead they
 * can be found in the html.tpl.php template in this directory.
 *
 * Available variables:
 *
 * General utility variables:
 * - $base_path: The base URL path of the Drupal installation. At the very
 *   least, this will always default to /.
 * - $directory: The directory the template is located in, e.g. modules/system
 *   or themes/bartik.
 * - $is_front: TRUE if the current page is the front page.
 * - $logged_in: TRUE if the user is registered and signed in.
 * - $is_admin: TRUE if the user has permission to access administration pages.
 *
 * Site identity:
 * - $front_page: The URL of the front page. Use this instead of $base_path,
 *   when linking to the front page. This includes the language domain or
 *   prefix.
 * - $logo: The path to the logo image, as defined in theme configuration.
 * - $site_name: The name of the site, empty when display has been disabled
 *   in theme settings.
 * - $site_slogan: The slogan of the site, empty when display has been disabled
 *   in theme settings.
 *
 * Navigation:
 * - $main_menu (array): An array containing the Main menu links for the
 *   site, if they have been configured.
 * - $secondary_menu (array): An array containing the Secondary menu links for
 *   the site, if they have been configured.
 * - $breadcrumb: The breadcrumb trail for the current page.
 *
 * Page content (in order of occurrence in the default page.tpl.php):
 * - $title_prefix (array): An array containing additional output populated by
 *   modules, intended to be displayed in front of the main title tag that
 *   appears in the template.
 * - $title: The page title, for use in the actual HTML content.
 * - $title_suffix (array): An array containing additional output populated by
 *   modules, intended to be displayed after the main title tag that appears in
 *   the template.
 * - $messages: HTML for status and error messages. Should be displayed
 *   prominently.
 * - $tabs (array): Tabs linking to any sub-pages beneath the current page
 *   (e.g., the view and edit tabs when displaying a node).
 * - $action_links (array): Actions local to the page, such as 'Add menu' on the
 *   menu administration interface.
 * - $feed_icons: A string of all feed icons for the current page.
 * - $node: The node object, if there is an automatically-loaded node
 *   associated with the page, and the node ID is the second argument
 *   in the page's path (e.g. node/12345 and node/12345/revisions, but not
 *   comment/reply/12345).
 *
 * Regions:
 * - $page['help']: Dynamic help text, mostly for admin pages.
 * - $page['highlighted']: Items for the highlighted content region.
 * - $page['content']: The main content of the current page.
 * - $page['sidebar_first']: Items for the first sidebar.
 * - $page['sidebar_second']: Items for the second sidebar.
 * - $page['header']: Items for the header region.
 * - $page['footer']: Items for the footer region.
 *
 * @see bootstrap_preprocess_page()
 * @see template_preprocess()
 * @see template_preprocess_page()
 * @see bootstrap_process_page()
 * @see template_process()
 * @see html.tpl.php
 *
 * @ingroup themeable
 */
?>
<div id="page_wrapper">
<?php include("/var/www/resources/templates/body-navigation.php"); /* YTP common navigation */ ?>


<?php if (!empty($page['highlighted'])): ?>
  <div class="container">
    <div class="alert alert-info" role="alert"><?php print render($page['highlighted']); ?></div>
  </div>
<?php endif; ?>
<div class="container toolbar drupal-crumbs">
 <?php if (!empty($breadcrumb)): print $breadcrumb; endif;?>
 </div>
<div class="main-container container">
  <header role="banner" id="page-header">
    <?php if (!empty($site_slogan)): ?>
      <p class="lead"><?php print $site_slogan; ?></p>
    <?php endif; ?>
    <?php if (!empty($page['header'])): ?>
      <div class="row hidden-xs hidden-sm">
        <?php if (!empty($page['top_bar_secondary'])): ?>
          <div class="col-lg-9">
            <?php print render($page['header']); ?>
          </div>
          <div class="col-lg-3" id="infobox">
            <?php print render($page['top_bar_secondary']); ?>
          </div>
        <?php else: ?>
          <div class="col-lg-12">
            <?php print render($page['header']); ?>
          </div>
        <?php endif; ?>
      </div>
    <?php endif; ?>

  </header> <!-- /#page-header -->


  <div class="row">
    <?php if (!empty($page['sidebar_first'])): ?>
      <aside class="col-xs-12 col-sm-12 col-md-12 col-lg-3 ytp-nav" role="complementary">
        <?php print render($page['sidebar_first']); ?>
      </aside>  <!-- /#sidebar-first -->
    <?php endif; ?>

    <section<?php print $content_column_class; ?>>
      <?php
        if (isset($ytp_custom_top)) {
          print $ytp_custom_top;
        }
      ?>
    <?php if (!user_is_logged_in()) { ?>
      <div id="responsive-login-panel" class="panel panel-default visible-xs visible-sm visible-md">
        <div class="panel-body">
            <a href="<?php print url('user/login')?>"> <?php print t('Sign up or log in') ?></a>
        </div>
      </div>
    <?php } ?>

    <?php
        #if we are on the front page
        if (isset($ytp_custom_top)) {
    ?>
        <div id="responsive-browse-panel" class="panel panel-default visible-xs visible-sm visible-md">
          <div class="panel-body">
            <a href="<?php print "data/" . $language->language . "/dataset" ?>"> <?php print t('Browse datasets') ?></a>
          </div>
        </div>
    <?php
      }
    ?>
      <a id="main-content"></a>
      <?php print render($title_prefix); ?>
      <?php if (!empty($title)): ?>
        <h1 class="page-header"><?php print $title; ?></h1>
      <?php endif; ?>
      <?php print render($title_suffix); ?>
      <?php print $messages; ?>
      <?php if (!empty($tabs)): ?>
        <?php print render($tabs); ?>
      <?php endif; ?>
      <?php if (!empty($page['help'])): ?>
        <?php print render($page['help']); ?>
      <?php endif; ?>
      <?php if (!empty($action_links)): ?>
        <ul class="action-links"><?php print render($action_links); ?></ul>
      <?php endif; ?>
      <?php print render($page['content']); ?>
    </section>

    <?php if (!empty($page['sidebar_second'])): ?>
      <aside class="col-sm-4" role="complementary">
        <?php print render($page['sidebar_second']); ?>
      </aside>  <!-- /#sidebar-second -->
    <?php endif; ?>

  </div>
</div>
</div>
<footer class="footer container">
  <?php print render($page['footer']); ?>
</footer>


