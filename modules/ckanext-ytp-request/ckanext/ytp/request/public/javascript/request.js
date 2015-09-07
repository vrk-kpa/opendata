$(document).ready(function() {
    $('#field-organizations').on('change', function(e) {
   	    ckan.sandbox().client.call('POST', 'get_available_roles', {organization_id: $("#field-organizations option:selected").text()}, function(results) {
        	var roles = $('#role');
        	//Remove old values
        	roles.get(0).options.length = 0;
        	//Populate with news
        	var result = results['result'];
        	$.each(result, function(key, val) {
        		roles.get(0).options[roles.get(0).options.length] = new Option(val.text, val.value);
        	});
        });$
   });
});
