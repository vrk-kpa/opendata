# CUSTOM MODULES FOR DRUPAL

This document describes how to initialize and use our custom Drupal modules.

Status: work in progress

## YTP-DRUPAL-FEATURES

  ### ARTICLE_FEATURE
  Work in progress

  ### ARTICLE_VIEW_FEATURE
  Work in progress

  ### BLOCKS_FEATURE
  Work in progress

  ### CALENDAR_FEATURE
  Work in progress

  ### FEATURE_BLOCKS_FEATURE

    Creates features region on front page, consisting of
      - Twitter feed
      - list of recent datasets
      - list of popular datasets
      - links to related sites

    Dependencies: ytp-theme-drupal (for theme and translations)

    #### Initialization

      0. The feature is installed by Ansible. 

      1. Twitter feed
        Create a Twitter widget to get a Twitter data-widget-id. See 
        [Twitter widgets](https://twitter.com/settings/widgets) as logged in Twitter user.

        Go to Structure -> Blocks -> Add Twitter block. Fill required fields. For region settings, 
        choose "YTP theme": "Feature blocks". For pages, choose "Only the listed pages": "<front>".

      2. New/popular datasets
        Should be good to go. If a block is empty, going to Structure -> Blocks -> (block name) -> 
        Configure and saving the configuration should fix it.

      3. Related links
        Go to Structure -> Blocks -> Add menu block. Select "Menu": "Related links" and region 
        setting "YTP theme": "Feature blocks". For pages, choose "Only the listed pages": "<front>". 
        Make the block translatable. Set and translate the block title manually.

        The block won't be shown unless there's at least one link in the menu. Go to Structure -> Menus -> Related sites to add links. All links should have language.

      4. Block order
        See Structure -> Blocks.

    #### Editing

      1. Twitter feed
        Structure -> Blocks -> (block name) -> Configure, or just edit the widget via Twitter.

      2. New/popular datasets
        The data is fetched via CKAN API. The PHP code to do it is located in the block body.

        Block titles can be translated using the .pot and .po files in ytp-theme-drupal/i18n-blocks.

      3. Related links
        Links can be added, edited and deleted at Structure -> Menus -> Related sites. All links
        should have a language.

      4. General theme
        To move feature blocks region in relation to other regions, see 
        ytp-theme-drupal/templates/page--front.tpl.php.

        To edit the look of all blocks in feature blocks region, see
        ytp-theme-drupal/templates/block--feature_blocks.tpl.php.

        To edit blocks in feature blocks region in CSS/jQuery, a possible selector could be 
        .feature-blocks .panel.

  ### FRONTPAGE_CAROUSEL_FEATURE
  Work in progress

  ### FRONTPAGE_INFOBOX_FEATURE
  Work in progress

  ### FRONTPAGE_TUTORIAL
  Work in progress

  ### LANGUAGE_FEATURE
  Work in progress

  ### SERVICE_ALERT_FEATURE
  Work in progress

## YTP-DRUPAL-USER
Work in progress

## YTP-THEME-DRUPAL
Work in progress
