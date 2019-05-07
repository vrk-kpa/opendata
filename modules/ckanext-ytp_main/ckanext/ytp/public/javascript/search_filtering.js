document.onreadystatechange = function () {
  if (document.readyState == "interactive") {
    document.getElementById("search-filter-show-button").addEventListener("click", toggle_search_filters);
    document.getElementById("search-filter-upper-hide-button").addEventListener("click", toggle_search_filters);
    document.getElementById("search-filter-lower-hide-button").addEventListener("click", toggle_search_filters);

    const search_filters = document.getElementsByClassName("sidebar-offcanvas")[0];
    const upper_hide_button = document.getElementById("search-filter-upper-hide-button");
    const lower_hide_button = document.getElementById("search-filter-lower-hide-button");
    const show_button = document.getElementById("search-filter-show-button");

    // If url parameter exists, the search filters and both 'hide filters' buttons are shown.
    if (window.location.search.indexOf("_show_search_filters=true") > -1) {
      search_filters.classList.remove("search-filters-hidden");
      search_filters.classList.add("search-filters-visible");
      upper_hide_button.classList.add("hide-button-visible");
      lower_hide_button.classList.add("hide-button-visible");
      show_button.classList.add("show-button-hidden");
    }
  }
}

/**
 * If search filters are hidden, they become visible. If they are visible, they will become hidden.
 * Classes for buttons are updated as well so that the correct buttons are visible.
 */
function toggle_search_filters() {
  const search_filters = document.getElementsByClassName("sidebar-offcanvas")[0];
  const upper_hide_button = document.getElementById("search-filter-upper-hide-button");
  const lower_hide_button = document.getElementById("search-filter-lower-hide-button");
  const show_button = document.getElementById("search-filter-show-button");

  if (search_filters.classList.contains("search-filters-hidden")) {
    search_filters.classList.remove("search-filters-hidden");
    search_filters.classList.add("search-filters-visible");
    upper_hide_button.classList.add("hide-button-visible");
    lower_hide_button.classList.add("hide-button-visible");
    show_button.classList.add("show-button-hidden");
    updateURLParameter("_show_search_filters", "true");
    update_search_filter_parameter_to_links("true");
  } else {
    search_filters.classList.remove("search-filters-visible");
    search_filters.classList.add("search-filters-hidden");
    upper_hide_button.classList.remove("hide-button-visible");
    lower_hide_button.classList.remove("hide-button-visible");
    show_button.classList.remove("show-button-hidden");
    updateURLParameter("_show_search_filters", "false");
    update_search_filter_parameter_to_links("false");
  }
}

/**
 * Update all the links to the current page with the new '_show_search_filters' URL parameter value.
 * Links to the current page are filter links that are used in the facet.
 * @param show_search_filters_value The value for the _show_search_filters URL parameter. Should be either 'true' or 'false'
 */
function update_search_filter_parameter_to_links(show_search_filters_value) {
  const all_links = document.links;
  for (let i=0; i<all_links.length; i++) {
    const href_value = all_links[i].href;
    const link_without_url_parameters = href_value.split("?")[0];
    const current_page_without_url_parameters = location.href.split("?")[0];
    if (current_page_without_url_parameters === link_without_url_parameters) {
      const new_url_parameters = get_url_with_updated_parameter(href_value, "_show_search_filters", show_search_filters_value).split("?")[1];
      all_links[i].href = "dataset?" + new_url_parameters;
    }
  }
}

/**
 * Changes the url by updating the given URL parameter
 * @param param The url parameter that will be changed
 * @param param_val The new value for the url parameter
 */
function updateURLParameter(param, param_val) {
  const url = window.location.href;
  const new_url = get_url_with_updated_parameter(url, param, param_val)
  window.history.replaceState("", "", new_url);
}

/**
 * http://stackoverflow.com/a/10997390/11236
 * This function changes the url by changing the value of the given url parameter and returns the new url
 * @param url The url to be changed
 * @param param The url parameter that will be changed
 * @param paramVal The new value for the url parameter
 */
function get_url_with_updated_parameter(url, param, paramVal) {
    let theAnchor = null;
    let newAdditionalURL = "";
    let tempArray = url.split("?");
    let baseURL = tempArray[0];
    let additionalURL = tempArray[1];
    let temp = "";

    if (additionalURL) {
      let tmpAnchor = additionalURL.split("#");
      let theParams = tmpAnchor[0];
      theAnchor = tmpAnchor[1];
      if (theAnchor) {
        additionalURL = theParams;
      }
      tempArray = additionalURL.split("&");
      for (let i=0; i<tempArray.length; i++) {
        if (tempArray[i].split("=")[0] != param) {
          newAdditionalURL += temp + tempArray[i];
          temp = "&";
        }
      }
    } else {
      let tmpAnchor = baseURL.split("#");
      let theParams = tmpAnchor[0];
      theAnchor  = tmpAnchor[1];

      if (theParams) {
        baseURL = theParams;
      }
    }

    if (theAnchor) {
      paramVal += "#" + theAnchor;
    }

    let rows_txt = temp + "" + param + "=" + paramVal;
    return baseURL + "?" + newAdditionalURL + rows_txt;
}
