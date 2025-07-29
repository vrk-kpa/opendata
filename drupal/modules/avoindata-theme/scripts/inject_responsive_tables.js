var injectResponsiveTables = function (next) {
  document.addEventListener('readystatechange', function () {
    if (document.readyState == "interactive" || document.readyState == "complete") {
      var content = document.getElementsByClassName("region-content");
      if (content.length != 0) {
        var sections = content[0].getElementsByClassName("avoindata-section-content");
        for ( var j = 0; j < sections.length; j++) {
          var tables = sections[j].getElementsByTagName("table");
          for (var i = 0; i < tables.length; ++i) {
            if(tables[i].parentElement.classList.contains('table-responsive')) {
              continue;
            }
            var wrapper = document.createElement("div");
            tables[i].classList.add("table");
            wrapper.classList.add("table-responsive");
            tables[i].parentElement.insertBefore(wrapper, tables[i]);
            wrapper.appendChild(tables[i]);
          }
        }
      }
    }
    if(next) {
      next();
    }
  })
}(document.onreadystatechange);
