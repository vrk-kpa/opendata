$(document).ready(function() {
    $('#field-validroles').on('change', function(e) {
      var selected_role = $("#field-validroles option:selected").text();
      //Modify the URLs for accept and reject cases
      var approve_url_element = $('#request_approve_url');
      var reject_url_element = $('#request_reject_url');
      var approve_url = approve_url_element.getAttribute('href').split('&', 2);
      var reject_url = reject_url_element.getAttribute('href').split('&',2);
      newapp_url = approve_url[0] + '&role=' + selected_role;
      newrej_url = reject_url[0] +  '&role=' + selected_role;
      approve_url_element.setAttribute('href', newapp_url);
      reject_url.element.setAttribute('href', newrej_url);
    });
    
    $('#field-organizations').on('change', function(e) {
   	    //Setting the default selected roleto admin (in case editor was selected and now does not exist)
 		var roles = $('#role');
   	    roles.val("admin").trigger("change");
   	    ckan.sandbox().client.call('POST', 'get_available_roles', {organization_id: $("#field-organizations option:selected").text()}, function(results) {
        	var roles = $('#role');
        	//Remove old values
        	roles.get(0).options.length = 0;
        	//Populate with news
        	var result = results['result'];
        	$.each(result, function(key, val) {
        		roles.get(0).options[roles.get(0).options.length] = new Option(val.text, val.value);
        	}); 
        });
   }); 
});
