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

## YTP-DRUPAL-FOOTER

  Creates content for page footer region. Contains (1) an editable block for free text, 
  (2) a menu block for links and (3) a block for social media buttons.

  Dependencies: ytp-theme-drupal (for styling)
                menu-block (for links)

  ### Initialization

    0. The feature is installed by Ansible.

    1. Site owner info block
      Make block content translatable: Configuration -> Regional and language -> 
      Multilingual settings. Click on "Variables" tab. Select variable Other -> Site owner info 
      and save.

      Make text format translatable: Configuration -> Regional and language -> 
      Multilingual settings. Click on "Strings" tab. Select text format you will use for the block
      ("Filtered HTML" being default value) and save.

      Set block content as variable at Configuration -> System -> Variables. The variable to 
      translate is Other -> Site owner info.

    2. Link block
      Make the menu translatable at Structure -> Menus -> Footer links -> Multilingual options.

      The block won't be shown unless there's at least one link in the menu. Go to Structure -> 
      Menus -> Footer links to add links. All links should have language.

      Note that you shouldn't place any links to restricted content (ie. admin pages) in the 
      footer, as they won't be displayed in CKAN.

    3. Social media icons block
      Get the HTML codes from your preferred social media sites. Go to Structure -> Blocks -> 
      Social media icons, make sure to turn rich text editing off and switch text format to full 
      HTML and paste your codes to the "Icon source code" box. This block will not be translated, 
      so avoid writing any text.

  ### Editing

    1. Site owner info block
      Edit content at Configuration -> System -> Variables. The variable to edit is Other -> 
      Site owner info.

    2. Link block
      Add or remove links at Structures -> Menus -> Footer links.

    3. Social media icons block
      Edit at Structure -> Blocks -> Social media icons. Make sure to turn off rich text editing 
      and switch text format to full HTML.

    4. General theme
      CSS is located at ytp-assets-common/src/less/common.less.

      To edit the look of all blocks, see ytp-theme-drupal/templates/block--footer.tpl.php.

## YTP_DRUPAL_FRONTPAGE

  Creates following front page features:
    - list of recent news (blog posts)
    - Twitter feed
    - list of recent datasets
    - list of popular datasets
    - links to related sites

  Dependencies: ytp-theme-drupal (for theme and translations)
                ytp-assets-common (for styling)
                views (for news)
                menu-block (for related sites)

  #### Initialization

    0. The feature is installed by Ansible. 

    1. News
      Should be good to go.

    2. Twitter feed
      Create a Twitter widget to get a Twitter data-widget-id. See 
      [Twitter widgets](https://twitter.com/settings/widgets) as logged in Twitter user.
      Go to Config -> Variables -> Other and set variable Twitter Widget ID with the value of 
      your data-widget-id.

    3. New/popular datasets
      Should be good to go.

    4. Related links
      The block won't be shown unless there's at least one link in the menu. Go to Structure -> 
      Menus -> Related sites to add links. All links should have language.

    5. Block order
      See Structure -> Blocks.

  #### Editing

    1. News
      Can be edited at Structure -> Views -> News, but you probably shouldn't, as these changes 
      won't be propagated to other installations. If possible, edit 
      ytp-drupal-frontpage/ytp_frontpage.module.

    2. Twitter feed
      Can only be edited at ytp-drupal-frontpage/ytp_frontpage.module.

    3. New/popular datasets
      Can only be edited at ytp-drupal-frontpage/ytp_frontpage.module.

    4. Related links
      Links can be added, edited and deleted at Structure -> Menus -> Related sites. All links
      should have a language.

    5. General theme
      To change block icons, see function ytp_frontpage_preprocess_block() at 
      ytp-drupal-frontpage/ytp_frontpage.module.

      To edit the CSS of the blocks, see ytp-assets-common/src/less/drupal/drupal.less. They can 
      be accessed with selectors ".region-content-grid-left .block" and 
      ".region-content-grid-right .block".

## YTP-DRUPAL-TUTORIAL

  Creates a tutorial block on front page. The block will determine if user is registered, belongs 
  to an organization and/or has published data, and show matching instructions. User can opt out 
  of seeing some views.

  Dependencies: ytp-drupal-user (module reads and edits some fields created by ytp-drupal-user)
                ytp-theme-drupal (for styling)

  ### Initialization

    0. The feature is installed by Ansible.

    1. Block settings
      Structure -> Blocks -> Front page tutorial -> Configure. Set block title to <none>. 
      For pages, choose "Only the listed pages": "<front>".

  ### Editing

    1. Content
    Each view has a content function located in ytp_tutorial.module: 
    ytp_tutorial_get_data_not_logged_in(), ytp_tutorial_get_data_no_organization(), 
    ytp_tutorial_get_data_no_published_datasets(), ytp_tutorial_get_data_tools(). These functions
    set three variables that are passed to template: title (translatable string), image_url 
    (/path/to/file) and content (Drupal render array).

    2. Translations
    The module comes with its own .po and .pot files under directory "i18".

    3. Theme
    To edit the look of all the views, see ytp_tutorial.tpl.php.

    To edit the CSS of the block, see ytp-assets-common/src/less/drupal/drupal.less. It can be 
    accessed with selector #tutorial-box.

## YTP-DRUPAL-USER
Work in progress

## YTP-THEME-DRUPAL
Work in progress
