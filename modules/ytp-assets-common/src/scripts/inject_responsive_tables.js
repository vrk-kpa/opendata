var injectResponsiveTables = function (next) {
  document.onreadystatechange = function () {
    if (document.readyState == "interactive") {
      var article = document.getElementById("block-system-main");
      if(article !== null) {
        var tables = article.getElementsByTagName("table");
        for (var i = 0; i < tables.length; ++i) {
          var wrapper = document.createElement("div");
          if(tables[i].border === "0") {
            tables[i].classList.add("table");
          }
          wrapper.classList.add("table-responsive");
          tables[i].parentElement.insertBefore(wrapper, tables[i]);
          wrapper.appendChild(tables[i]);
        }
      }
    }
    if(next) {
      next();
    }
  }
}(document.onreadystatechange);
