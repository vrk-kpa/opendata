var CKANEXT = CKANEXT || {};
CKANEXT.QA = CKANEXT.QA || {};

(function(ns, $){
    ns.init = function(packageName, apiEndpoint){
        // a call to apiEndpoint should return a list of all
        // resources for this package and their availability
        //
        // go through each resource and link to a cached copy
        // if not available
        var success = function(response){
            for(var i in response.resources){
                ns.checkResourceAvailability(response.resources[i]);
            }
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

    ns.checkResourceAvailability = function(resource){
        if(resource['resource_available'] === 'false'){
            // make sure this resource has a hash value
            var hash = resource['resource_hash'];
            if(hash.length == 0){
                return;
            }
            if(resource['resource_cache'].length == 0){
                return;
            }

            // find the table row corresponding to this resource
            var td = $('.resources').find('td:contains("' + hash + '")');
            if(td.length == 0){
                return;
            }
            var row = td.closest('tr');

            // add a new row after this one containing a link to the cached resource
            var cacheHtml = '<tr><td class="cached-resource" colspan="4">' + 
                'This resource may be missing. ' +
                '<a href="' + resource['resource_cache'] + '">' +
                'Click here to download a cached copy</a>' +
                '</td></tr>';
            row.after(cacheHtml);
        }
    };

})(CKANEXT.QA, jQuery);
