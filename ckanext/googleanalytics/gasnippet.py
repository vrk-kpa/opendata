header_code = """
<script type="text/javascript">
  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', '%s']);
  _gaq.push(['_setDomainName', '%s']);
  _gaq.push(['_trackPageview']);
  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();
</script>
"""

footer_code = """
<script type="text/javascript" src="%s"></script>
"""

download_style = """
<style type="text/css">
   span.downloads-count {
   font-size: 0.9em;
   }
</style>
"""
