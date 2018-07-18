'use strict';

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    addEventSearchClickListeners();
  }
}

function addEventSearchClickListeners() {
  var searchButton = document.getElementById('avoindata-events-search-btn');
  searchButton.onclick = searchEventsSubmit;
}

function searchEventsOnEnter() {
  if(event.key === 'Enter') {
    searchEventsSubmit();
  }
}

function searchEventsSubmit() {
  var searchInput = document.getElementById('avoindata-events-search-input');
  var selectElem = document.getElementById("avoindata-events-search-sort");
  var sortOrder = selectElem.options[selectElem.selectedIndex].value || 'desc';
  if(searchInput.value) {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/events/' + sortOrder + '/' + searchInput.value);
  } else {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/events/' + sortOrder);
  }
}
