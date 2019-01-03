document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    // If client is not blocking js we show the search inputs
    document.getElementById('header-search-container').hidden = false;
    addHeaderSearchListeners();
  }
};

function addHeaderSearchListeners() {
  let searchInput = document.getElementById('avoindata-nav-search-input');
  searchInput.onkeyup = onHeaderSearchInput;
}

function onHeaderSearchInput(event) {
  if (event.keyCode == 13) {
    let searchInput = document.getElementById('avoindata-nav-search-input');
    let currentLanguage = searchInput.dataset.langauge || 'fi';
    currentLanguage = (currentLanguage === 'en') ? 'en_GB' : currentLanguage;
    window.location.replace(`${window.location.origin}/data/${currentLanguage}/dataset?q=${encodeURI(searchInput.value)}`);
  }
}
