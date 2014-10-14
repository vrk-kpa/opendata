<?php

function ytp_theme_links__locale_block(&$variables) {
  global $language;
  $items = array();
  // var_dump($variables);
  foreach($variables['links'] as $lang => $info) {
      $name = $info['language']->native;
      $href = isset($info['href']) ? $info['href'] : '';
      $li_classes = array('list-item-class');
      if($lang === $language->language){
            // $li_classes[] = 'active';
      }
      $options = array('attributes' => array(), 'language' => $info['language'], 'html' => true);
      if (!$href) {
          $options['attributes'] = array('class' => array('locale-untranslated'));
      }
      $link = l($name, $href, $options);
      $items[] = array('data' => $link, 'class' => $li_classes);
  }
  $attributes = array('class' => array('nav', 'navbar-nav', 'lang-select'));
  $output = theme_item_list(array('items' => $items,
                                  'title' => '',
                                  'type'  => 'ul',
                                  'attributes' => $attributes
                                  ));
  return $output;
}


/**
 * Implements hook_preprocess_page().
 *
 * @see page.tpl.php
 */
function ytp_theme_preprocess_page(&$variables) {
  // Add information about the number of sidebars.
  if (isset($_COOKIE['Drupal_visitor_ytp_logoff']) && $_COOKIE['Drupal_visitor_ytp_logoff'] == 1) {
    drupal_set_message(t('Thank you for visiting. You are now logged out.'));
    user_cookie_save(array('ytp.logoff' => 0));
  }

  if (!empty($variables['page']['sidebar_first']) && !empty($variables['page']['sidebar_second'])) {
    $variables['content_column_class'] = ' class="col-sm-4"';
  }
  elseif (!empty($variables['page']['sidebar_first']) || !empty($variables['page']['sidebar_second'])) {
    $variables['content_column_class'] = ' class="col-sm-8"';
  }
  else {
    $variables['content_column_class'] = ' class="col-sm-12"';
  }

  // Primary nav.
  $variables['primary_nav'] = FALSE;
  if ($variables['main_menu']) {
    // Build links.
    $variables['primary_nav'] = menu_tree(variable_get('menu_main_links_source', 'main-menu'));
    // Provide default theme wrapper function.
    $variables['primary_nav']['#theme_wrappers'] = array('menu_tree__primary');
  }

  // Secondary nav.
  $variables['secondary_nav'] = FALSE;
  if ($variables['secondary_menu']) {
    // Build links.
    $variables['secondary_nav'] = menu_tree(variable_get('menu_secondary_links_source', 'user-menu'));
    // Provide default theme wrapper function.
    $variables['secondary_nav']['#theme_wrappers'] = array('menu_tree__secondary');
  }

  $variables['navbar_classes_array'] = array('navbar');

  if (theme_get_setting('bootstrap_navbar_position') !== '') {
    $variables['navbar_classes_array'][] = 'navbar-' . theme_get_setting('bootstrap_navbar_position');
  }
  else {
    $variables['navbar_classes_array'][] = 'container';
  }
  if (theme_get_setting('bootstrap_navbar_inverse')) {
    $variables['navbar_classes_array'][] = 'navbar-inverse';
  }
  else {
    $variables['navbar_classes_array'][] = 'navbar-default';
  }

  $site_section = menu_get_active_trail();
  if (array_key_exists(1, $site_section)){
    $variables['site_section'] = $site_section[1]['title'];
  }
  else{
    $variables['site_section'] = '';
  }

  // Hide edit tabs from user login and register pages
  if (in_array('page__user__login', $variables['theme_hook_suggestions']) or in_array('page__user__register', $variables['theme_hook_suggestions'])){
    unset($variables['tabs']);
  }

  // Customize login page
  if ( in_array('page__user__login', $variables['theme_hook_suggestions'] ) ){
    $loginform = drupal_get_form('user_login_block');
    if (variable_get('user_register', USER_REGISTER_VISITORS_ADMINISTRATIVE_APPROVAL)) {
        $items[] = l(t('Create new account'), 'user/register', array('attributes' => array('title' => t('Create a new user account.'))));
    }
    $items[] = '<a onclick="jQuery(\'#ResetPasswordForm\').show()">' . t("Request new password") . '</a>';
    $loginform['links'] = array('#markup' => theme('item_list', array('items' => $items)));
    $loginform['links']['#weight'] = 100;
    $loginform['#attributes'] = array('class' => 'form-horizontal');
    $loginform['name']['#field_prefix'] = '<div class="col-sm-10">';
    $loginform['name']['#field_suffix'] = '</div>';

    $loginform['pass']['#field_prefix'] = '<div class="col-sm-10">';
    $loginform['pass']['#field_suffix'] = '</div>';

    $loginform['links']['#prefix'] = '<div class="col-sm-8">';
    $loginform['links']['#suffix'] = '</div></div>';

    $loginform['actions']['#prefix'] = '<div class="col-sm-2 col-sm-offset-2">';
    $loginform['actions']['#suffix'] = '</div>';

    #$loginform['actions']['#weight'] = 0;

    // Map CKAN-style 'came_from' redirects to use Drupal's 'destination' param
    if (isset($_GET['came_from'])) {
      $loginform_query_string = array('destination' => $_GET['came_from']);
      $loginform['#action'] = url('user/login', array('query' => $loginform_query_string));
    }

    $variables['loginform'] = $loginform;

    $resetform = drupal_get_form('user_pass');
    $resetform_query_string = array('destination' => 'user/login');
    $resetform['#action'] = url('user/password', array('query' => $resetform_query_string));

    $resetform['#attributes'] = array('class' => 'form-horizontal');
    $resetform['name']['#field_prefix'] = '<div class="col-sm-10">';
    $resetform['name']['#field_suffix'] = '</div>';
    $resetform['actions']['#prefix'] = '<div class="form-group"><div class="col-sm-10 col-sm-offset-2">';
    $resetform['actions']['#suffix'] = '</div></div>';
    $variables['resetform'] = $resetform;
  }
}

/**
 * Implements hook_process_page().
 *
 * @see page.tpl.php
 */
function ytp_theme_process_page(&$variables) {
  $variables['navbar_classes'] = implode(' ', $variables['navbar_classes_array']);
}

/**
 * Override or insert variables into the html template.
 */
function ytp_theme_preprocess_html(&$variables) {
   switch (theme_get_setting('bootstrap_navbar_position')) {
       case 'fixed-top':
         $variables['classes_array'][] = 'navbar-is-fixed-top';
         break;

       case 'fixed-bottom':
         $variables['classes_array'][] = 'navbar-is-fixed-bottom';
         break;

       case 'static-top':
         $variables['classes_array'][] = 'navbar-is-static-top';
         break;
   }
   $domain = "avoindata.fi";
   if (!empty($_SERVER['HTTP_HOST']) && !is_numeric($_SERVER['HTTP_HOST'][0])) {
    $domain = implode('.', array_slice(explode('.', $_SERVER['HTTP_HOST']), -2));
   }

    $title = drupal_get_title();
    if ( $title == '' ){
        $variables['head_title'] = $domain;
    }
    else{
        $variables['head_title'] = implode(' - ', array(drupal_get_title(), $domain));
    }

}

/**
 * Overrides theme_menu_link().
 * This fixes hierarchical vertical block menus when using Bootstrap theme.
 */
function ytp_theme_menu_link(&$variables) {
  $element = $variables['element'];
  $sub_menu = '';

  if (isset($element['#bid']) && ($element['#bid']['module'] == 'menu_block')) {
      $element['#attributes']['class'][] = 'ytp-menulink';
  }

  if ($element['#below']) {

    // Prevent dropdown functions from being added to management menu so it does not affect the navbar module.
    if (($element['#original_link']['menu_name'] == 'management' && module_exists('navbar'))
        || ((!empty($element['#original_link']['depth']))
        && (isset($element['#bid']) && $element['#bid']['module'] == 'menu_block'))) {
            $sub_menu = drupal_render($element['#below']);
    }
    elseif ((!empty($element['#original_link']['depth'])) && ($element['#original_link']['depth'] == 1)) {
      // Add our own wrapper.
      unset($element['#below']['#theme_wrappers']);
      $sub_menu = '<ul class="dropdown-menu">' . drupal_render($element['#below']) . '</ul>';
      // Generate as standard dropdown.
      $element['#title'] .= ' <span class="caret"></span>';
      $element['#attributes']['class'][] = 'dropdown';
      $element['#localized_options']['html'] = TRUE;

      // Set dropdown trigger element to # to prevent inadvertant page loading when a submenu link is clicked.
      $element['#localized_options']['attributes']['data-target'] = '#';
      $element['#localized_options']['attributes']['class'][] = 'dropdown-toggle';
      $element['#localized_options']['attributes']['data-toggle'] = 'dropdown';
    }
  }
  // On primary navigation menu, class 'active' is not set on active menu item.
  // @see https://drupal.org/node/1896674
  if (($element['#href'] == $_GET['q'] || ($element['#href'] == '<front>' && drupal_is_front_page())) && (empty($element['#localized_options']['language']))) {
    $element['#attributes']['class'][] = 'active';
  }
  $output = l($element['#title'], $element['#href'], $element['#localized_options']);

  return '<li' . drupal_attributes($element['#attributes']) . '>' . $output . $sub_menu . "</li>\n";
}
/**
 * Overrides theme_breadcrumb().
 *
 * Print breadcrumbs as an ordered list.
 */
function ytp_theme_breadcrumb($variables) {
  $output = '';
  $breadcrumb = $variables['breadcrumb'];
  if($breadcrumb){
    if ($GLOBALS['language']->language=="fi"){
      $breadcrumb[0]="<a href=\"/fi\">Etusivu</a>";
    }else if ($GLOBALS['language']->language=="se"){
      $breadcrumb[0]="<a href=\"/se\">Start</a>";
    }
  }
  // Determine if we are to display the breadcrumb.
  $bootstrap_breadcrumb = theme_get_setting('bootstrap_breadcrumb');
  #  if (($bootstrap_breadcrumb == 1 || ($bootstrap_breadcrumb == 2 && arg(0) == 'admin')) && !empty($breadcrumb)) {
  if (($bootstrap_breadcrumb == 1 || $bootstrap_breadcrumb == 2 ) && !empty($breadcrumb)) {
    $output = theme('item_list', array(
      'attributes' => array(
        'class' => array('breadcrumb'),
      ),
      'items' => $breadcrumb,
      'type' => 'ol',
    ));
  }
  return $output;
}

function ytp_theme_form_alter(&$form, &$form_state, $form_id) {
  $function = "ytp_theme_{$form_id}_submit";
    if (function_exists($function)) {
        $form['#submit'][] = $function;
    }
    if ($form_id == 'user_profile_form') {
        $form['#submit'][] = 'ytp_theme_profile_form_submit';
    }
    if ($form_id === 'user_register_form') {
        $form['actions']['submit']['#suffix'] = '<span class="help-block" style="display: inline;">'
            . t('Next, you will get a confirmation email to your email address')
            . '</span><p class="help-block">'
            . t('By clicking Create new account, you agree with our <a href="/en/terms" target="_blank">Terms of Service</a>.') . '</p>';
    }
}

function ytp_theme_profile_form_submit($form, &$form_state) {
  global $language;
  $form_state['redirect'] = array('/data/' . $language->language . '/user/edit', array('external' => TRUE));
}

function ytp_theme_preprocess_node(&$variables){
    $date = format_date($variables['changed'], 'short');
    #todo get organization for username
    #$variables['submitted'] = t('Submitted by !username on !datetime', array('!username' => $variables['name'], '!datetime' =>$date));
    $user = user_load($variables['node']->uid);
    if ( isset($user->field_fullname['und']) && isset($user->field_fullname['und'][0]) && isset($user->field_fullname['und'][0]['value'])){
      $author = $user->field_fullname['und'][0]['value'];
    }
    else{
      $author = $variables['name'];
    }
    $variables['submitted'] = t('updated') . ' ' . t('!datetime | !username', array('!username' => $author, '!datetime' =>$date));
}

/**
 * Overrides theme_form_element().
 */
function ytp_theme_form_element(&$variables) {
  $element = &$variables['element'];
  $is_checkbox = FALSE;
  $is_radio = FALSE;

  // This function is invoked as theme wrapper, but the rendered form element
  // may not necessarily have been processed by form_builder().
  $element += array(
    '#title_display' => 'before',
  );

  // Add element #id for #type 'item'.
  if (isset($element['#markup']) && !empty($element['#id'])) {
    $attributes['id'] = $element['#id'];
  }
  $suffix = '';
  // Check for errors and set correct error class.
  if (isset($element['#parents']) && form_get_error($element)) {
    if ($element['#type'] != 'password_confirm' ){
      $suffix .= '<span class="control-full error-block">' . form_get_error($element) . '</span>';
    }
  }

  if (!empty($element['#type'])) {
    $attributes['class'][] = 'form-type-' . strtr($element['#type'], '_', '-');
  }
  if (!empty($element['#name'])) {
    $attributes['class'][] = 'form-item-' . strtr($element['#name'], array(
        ' ' => '-',
        '_' => '-',
        '[' => '-',
        ']' => '',
      ));
  }
  // Add a class for disabled elements to facilitate cross-browser styling.
  if (!empty($element['#attributes']['disabled'])) {
    $attributes['class'][] = 'form-disabled';
  }
  if (!empty($element['#autocomplete_path']) && drupal_valid_path($element['#autocomplete_path'])) {
    $attributes['class'][] = 'form-autocomplete';
  }
  $attributes['class'][] = 'form-item';

  // See http://getbootstrap.com/css/#forms-controls.
  if (isset($element['#type'])) {
    if ($element['#type'] == "radio") {
      $attributes['class'][] = 'radio';
      $is_radio = TRUE;
    }
    elseif ($element['#type'] == "checkbox") {
      $attributes['class'][] = 'checkbox';
      $is_checkbox = TRUE;
    }
    else {
      $attributes['class'][] = 'form-group';
    }
  }

  $description = FALSE;
  $tooltip = FALSE;
  // Convert some descriptions to tooltips.
  // @see bootstrap_tooltip_descriptions setting in _bootstrap_settings_form()
  if (!empty($element['#description'])) {
    $description = $element['#description'];
    if (theme_get_setting('bootstrap_tooltip_enabled') && theme_get_setting('bootstrap_tooltip_descriptions') && $description === strip_tags($description) && strlen($description) <= 200) {
      $tooltip = TRUE;
      $attributes['data-toggle'] = 'tooltip';
      $attributes['title'] = $description;
      $attributes['data-placement'] = 'top';
    }
  }

  $output = '<div' . drupal_attributes($attributes) . '>' . "\n";

  // If #title is not set, we don't display any label or required marker.
  if (!isset($element['#title'])) {
    $element['#title_display'] = 'none';
  }

  $prefix = '';

  if (isset($element['#field_prefix']) || isset($element['#field_suffix'])) {
    // Determine if "#input_group" was specified.
    if (!empty($element['#input_group'])) {
      $prefix .= '<div class="input-group">';
      $prefix .= isset($element['#field_prefix']) ? '<span class="input-group-addon">' . $element['#field_prefix'] . '</span>' : '';
      $suffix .= isset($element['#field_suffix']) ? '<span class="input-group-addon">' . $element['#field_suffix'] . '</span>' : '';
      $suffix .= '</div>';
    }
    else {
      $prefix .= isset($element['#field_prefix']) ? $element['#field_prefix'] : '';
      $suffix .= isset($element['#field_suffix']) ? $element['#field_suffix'] : '';
    }
  }

  switch ($element['#title_display']) {
    case 'before':
    case 'invisible':
      $output .= ' ' . theme('form_element_label', $variables);
      $output .= ' ' . $prefix . $element['#children'] . $suffix . "\n";
      break;

    case 'after':
      if ($is_radio || $is_checkbox) {
        $output .= ' ' . $prefix . $element['#children'] . $suffix;
      }
      else {
        $variables['#children'] = ' ' . $prefix . $element['#children'] . $suffix;
      }
      $output .= ' ' . theme('form_element_label', $variables) . "\n";
      break;

    case 'none':
    case 'attribute':
      // Output no label and no required marker, only the children.
      $output .= ' ' . $prefix . $element['#children'] . $suffix . "\n";
      break;
  }

  if ($description && !$tooltip) {
    $output .= '<p class="help-block">' . $element['#description'] . "</p>\n";
  }

  $output .= "</div>\n";

  return $output;
}

function ytp_theme_process_element(&$element, &$form_state){

  if (isset($element['#type']) && $element['#type'] === 'text_format'){
    if (isset($element['value']['#attributes']['data-toggle']) && $element['value']['#attributes']['data-toggle'] == 'tooltip'){
      $element['value']['#attributes']['data-placement'] = 'top';
    }
  }
}