'use strict';

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    addEventSearchClickListeners();
  }
}

function addEventSearchClickListeners() {
  const searchButton = document.getElementById('avoindata-events-search-btn');
  searchButton.onclick = searchEventsSubmit;
}

function searchEventsOnEnter() {
  if(event.key === 'Enter') {
    searchEventsSubmit();
  }
}

function searchEventsSubmit() {
  const searchInput = document.getElementById('avoindata-events-search-input');
  const selectElem = document.getElementById("avoindata-events-search-sort");
  const sortOrder = selectElem.options[selectElem.selectedIndex].value || 'desc';
  if(searchInput.value) {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/events/' + sortOrder + '/' + searchInput.value);
  }
}
