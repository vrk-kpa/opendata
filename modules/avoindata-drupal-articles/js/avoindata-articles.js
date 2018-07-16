'use strict';

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    addArticleSearchClickListeners();
  }
}

function addArticleSearchClickListeners() {
  const searchButton = document.getElementById('avoindata-articles-search-btn');
  searchButton.onclick = searchArticlesSubmit;
}

function searchArticlesSubmit() {
  const searchInput = document.getElementById('avoindata-articles-search-input');
  if(searchInput.value) {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/articles/' + searchInput.value);
  }
}
