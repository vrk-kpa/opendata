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

    Creates following front page features:
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
        choose "YTP theme": "Front Page Content Grid Left Side". For pages, choose "Only the listed pages": "<front>".

        On Structure -> Blocks page, ensure Twitter block is located under news view block.

      2. New/popular datasets
        Should be good to go. If a block is empty, going to Structure -> Blocks -> (block name) -> 
        Configure and saving the configuration should fix it.

      3. Related links
        Go to Structure -> Blocks -> Add menu block. Set "Title": "Twitter @avoindatafi". Select 
        all checkboxes under "Chrome". Set "Tweet limit": 2. Select "Menu": "Related sites" and 
        region setting "YTP theme": "Front Page Content Grid Right Side". For pages, choose "Only 
        the listed pages": "<front>". Make the block translatable. Set and translate the block 
        title manually.

        The block won't be shown unless there's at least one link in the menu. Go to Structure -> 
        Menus -> Related sites to add links. All links should have language.

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

## YTP-DRUPAL-FOOTER

  Creates content for page footer region. Contains (1) an editable block for free text, 
  (2) a menu block for links and (3) a block for social media buttons.

  Dependencies: ytp-theme-drupal (for styling)

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
