'use strict';

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    addArticleSearchClickListeners();
  }
}

function addArticleSearchClickListeners() {
  var searchButton = document.getElementById('avoindata-articles-search-btn');
  searchButton.onclick = searchArticlesSubmit;
}

function searchArticlesOnEnter() {
  if(event.key === 'Enter') {
    searchArticlesSubmit();
  }
}

function searchArticlesSubmit() {
  var searchInput = document.getElementById('avoindata-articles-search-input');
  if(searchInput.value) {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/articles?search=' + searchInput.value);
  } else {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/articles');
  }
}
