document.addEventListener('readystatechange', function () {
  if (document.readyState == "interactive") {
    document.getElementById("search-filter-show-button").addEventListener("click", toggle_search_filters);
    document.getElementById("search-filter-upper-hide-button").addEventListener("click", toggle_search_filters);
    document.getElementById("search-filter-lower-hide-button").addEventListener("click", toggle_search_filters);
  }
})

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
  } else {
    search_filters.classList.remove("search-filters-visible");
    search_filters.classList.add("search-filters-hidden");
    upper_hide_button.classList.remove("hide-button-visible");
    lower_hide_button.classList.remove("hide-button-visible");
    show_button.classList.remove("show-button-hidden");
  }
}
