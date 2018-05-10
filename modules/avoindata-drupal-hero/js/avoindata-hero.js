'use strict';
// Load polyfills
(function(undefined) {}).call('object' === typeof window && window || 'object' === typeof self && self || 'object' === typeof global && global || {});

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {

    addClickListeners();
    getCkanInformation();
  }
}

function addClickListeners() {
  const dropdownOptions = document.querySelectorAll('.dropdown-menu a');
  for (let i = 0; i < dropdownOptions.length; i++) {
    dropdownOptions[i].onclick = dropdownToggle;
  };
}

function dropdownToggle() {
  const allowedFilters = ['1', '2', '3'];
  const dropdown = document.querySelector('.btn-hero-dropdown');
  const selectedValue = this.getAttribute('data-value');
  dropdown.innerHTML = this.textContent + ' <span class="caret"></span>';
  dropdown.setAttribute('data-value', selectedValue);
  
  if(allowedFilters.indexOf(selectedValue > -1)) {
    document.querySelector('.input-hero-search-filter').value = selectedValue;
  }
}

function getCkanInformation() {
  setCountToBox('/data/api/3/action/package_list', '#avoindata-datasets-count');
  setCountToBox('/data/api/3/action/organization_list', '#avoindata-organizations-count');
  setCountToBox('/data/api/3/action/ckanext_showcase_list', '#avoindata-applications-count');
}

function setCountToBox(ckanUrl, documentSelector) {
  fetch(ckanUrl)
  .then(function(response) {
    return response.json();
  })
  .then(function(resJson) {
    if(resJson && resJson.result) {
      document.querySelector(documentSelector).innerHTML = resJson.result.length;
    }
  });
}
