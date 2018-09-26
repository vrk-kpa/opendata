'use strict';

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    addEventSearchClickListeners();
  }
}

function addEventSearchClickListeners() {
  var searchButton = document.getElementById('avoindata-events-search-btn');
  var selectSelector = document.getElementById('avoindata-events-search-sort');
  var showpastCheckbox = document.getElementById('avoindata-events-search-past');

  searchButton.onclick = searchEventsSubmit;
  selectSelector.onchange = searchEventsSubmit;
  showpastCheckbox.onchange = searchEventsSubmit;
}

function searchEventsOnEnter() {
  if(event.key === 'Enter') {
    searchEventsSubmit();
  }
}

function searchEventsSubmit() {
  var searchInput = document.getElementById('avoindata-events-search-input');
  var selectElem = document.getElementById('avoindata-events-search-sort');
  var showpastElem = document.getElementById('avoindata-events-search-past');
  var sortOrder = selectElem.options[selectElem.selectedIndex].value || 'desc';
  var showpast = showpastElem.checked || false;
  if(searchInput.value) {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/events?search=' + searchInput.value + '&sort=' + sortOrder + '&past=' + showpast);
  } else {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/events?sort=' + sortOrder + '&past=' + showpast);
  }
}
