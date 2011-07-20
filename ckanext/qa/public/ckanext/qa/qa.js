var CKANEXT = CKANEXT || {};
CKANEXT.QA = CKANEXT.QA || {};

(function(ns, $){
    ns.init = function(packageName, apiEndpoint){
        var success = function(response){
            console.log('success');
            console.log(response);
        };

        var error = function(response){
            var msg = "QA Error: Could not determine resource availability " +
                "for package " + packageName;
            console.log(msg);
        };

        $.ajax({method: 'GET',
                url: apiEndpoint,
                dataType: 'json',
                success: success,
                error: error
        }); 
    };

})(CKANEXT.QA, jQuery);
