'use strict';

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    addClickListeners();
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
