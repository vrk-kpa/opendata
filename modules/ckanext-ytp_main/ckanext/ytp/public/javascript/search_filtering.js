document.getElementById("search-filter-show-button").addEventListener("click", toggle_search_filters);
document.getElementById("search-filter-upper-hide-button").addEventListener("click", toggle_search_filters);
document.getElementById("search-filter-lower-hide-button").addEventListener("click", toggle_search_filters);

// If url parameter exists, the search filters and both 'hide filters' buttons are shown. 
if (window.location.search.indexOf("_show_search_filters=true") > -1) {
  var search_filters = document.getElementsByClassName("sidebar-offcanvas")[0];
  var upper_hide_button = document.getElementById("search-filter-upper-hide-button");
  var lower_hide_button = document.getElementById("search-filter-lower-hide-button");
  var show_button = document.getElementById("search-filter-show-button");
  search_filters.classList.remove("search-filters-hidden");
  search_filters.classList.add("search-filters-visible");
  upper_hide_button.classList.add("hide-button-visible");
  lower_hide_button.classList.add("hide-button-visible");
  show_button.classList.add("show-button-hidden");
}

function toggle_search_filters() {
  var search_filters = document.getElementsByClassName("sidebar-offcanvas")[0];
  var upper_hide_button = document.getElementById("search-filter-upper-hide-button");
  var lower_hide_button = document.getElementById("search-filter-lower-hide-button");
  var show_button = document.getElementById("search-filter-show-button");
  if (search_filters.classList.contains("search-filters-hidden")) {
    search_filters.classList.remove("search-filters-hidden");
    search_filters.classList.add("search-filters-visible");
    upper_hide_button.classList.add("hide-button-visible");
    lower_hide_button.classList.add("hide-button-visible");
    show_button.classList.add("show-button-hidden");
    updateURLParameter("_show_search_filters", "true");
  } else {
    search_filters.classList.remove("search-filters-visible");
    search_filters.classList.add("search-filters-hidden");
    upper_hide_button.classList.remove("hide-button-visible");
    lower_hide_button.classList.remove("hide-button-visible");
    show_button.classList.remove("show-button-hidden");
    updateURLParameter("_show_search_filters", "false");
  }
}

/**
 * http://stackoverflow.com/a/10997390/11236
 * This function changes the url by changing the value of the given url parameter
 * @param param The url parameter that will be changed
 * @param paramVal The new value for the url parameter
 */
function updateURLParameter(param, paramVal){
  var url = window.location.href;
  var newAdditionalURL = "";
  var tempArray = url.split("?");
  var baseURL = tempArray[0];
  var additionalURL = tempArray[1];
  var temp = "";
  if (additionalURL) {
      tempArray = additionalURL.split("&");
      for (var i=0; i<tempArray.length; i++){
          if(tempArray[i].split('=')[0] != param){
              newAdditionalURL += temp + tempArray[i];
              temp = "&";
          }
      }
  }

  var rows_txt = temp + "" + param + "=" + paramVal;
  var new_url = baseURL + "?" + newAdditionalURL + rows_txt;
  window.history.replaceState('', '', new_url);
}
