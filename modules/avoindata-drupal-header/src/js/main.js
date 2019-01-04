document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    // If client is not blocking js we show the search inputs
    document.getElementById('header-search-container').hidden = false;
    addHeaderSearchListeners();
  }
};

function addHeaderSearchListeners() {
  const searchSubmit = document.getElementById('avoindata-nav-search-submit');
  searchSubmit.onclick = onHeaderSubmitClick;
}

function onHeaderSubmitClick(event) {
  const searchInput = document.getElementById('avoindata-nav-search-input');
  const searchInputContainer = document.getElementsByClassName('header-search-input-container')[0];
  const searchForm = document.getElementById('header-search-form');
  if(searchInput.value.length > 0 && searchForm) {
    searchForm.submit();
  } else {
    searchInputContainer.classList.toggle('is-hidden');
  }
}
