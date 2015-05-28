<?php

function frontpage_tutorial_views_pre_view(&$view, &$display_id, &$args) {
	if ( $view->name == "frontpage_tutorial" ){
		if ( $display_id == 'authenticated_view' ){
			global $user;
			$temp = user_load($user->uid);
        if ( isset($temp->field_ckan_api_key['und']) && isset($temp->field_ckan_api_key['und'][0]) && isset($temp->field_ckan_api_key['und'][0]['value'])){
            $url = 'https://localhost/data/api/3/action/organization_list_for_user?permission=read';
            $options = array(
                'method' => 'GET',
                'headers' => array('Authorization' => $temp->field_ckan_api_key['und'][0]['value'])
            );
            $result = drupal_http_request($url, $options);
            $json = drupal_json_decode($result->data);
            if ( count($json['result']) > 1 ){
                $view->set_display('organization_member_view');
            }
        }
    }
  }
}

		
