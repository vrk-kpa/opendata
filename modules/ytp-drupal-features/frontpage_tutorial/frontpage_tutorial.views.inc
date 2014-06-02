<?php

function frontpage_tutorial_views_pre_view(&$view, &$display_id, &$args) {

	if ( $view->name == "frontpage_tutorial" ){
		dpm($view);
		dpm($display_id);
		if ( $display_id == 'block_1' ){
			global $user;
			dpm($user);	
			$temp = user_load($user->uid);
			dpm($temp);
			
if ( isset($temp->field_ckan_api_key['und']) && isset($temp->field_ckan_api_key['und'][0]) && isset($temp->field_ckan_api_key['und'][0]['value'])){
$url = 'http://localhost/data/api/3/action/organization_list_for_user?permission=read';
			$options = array(
				'method' => 'GET',
			
				'headers' => array('Authorization' => $temp->field_ckan_api_key['und'][0]['value'])
			);
			$result = drupal_http_request($url, $options);
			$json = drupal_json_decode($result->data);	
dpm($result);
dpm($json);
//$view->set_display('block_2');
dpm($json['result'][0]['id']);
if ( count($json['result']) == 1 && $json['result'][0]['id'] == 'yksityishenkilo'){
	$view->set_display('block_2');
}
}
}
}
}

		
