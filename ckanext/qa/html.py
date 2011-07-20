ORGANIZATION_LINK = '''<h3>%(link)s</h3>'''

HEAD_CODE = """
<link rel="stylesheet" href="/ckanext/qa/style.css" 
      type="text/css" media="screen" /> 
"""

JS_CODE = """
<script type="text/javascript" src="/ckanext/qa/qa.js"></script>
<script type="text/javascript">
    jQuery('document').ready(function($){
        CKANEXT.QA.init('%(package_name)s', '%(api_endpoint)s');
    });
</script>
"""
