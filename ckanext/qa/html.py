ORGANIZATION_LINK = '''<h3>%(link)s</h3>'''

QA_JS_CODE = """
<script type="text/javascript" src="/ckanext/qa/qa.js"></script>
<script type="text/javascript">
    jQuery('document').ready(function($){
        CKANEXT.QA.init();
    });
</script>
"""
