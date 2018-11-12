import queryString from 'query-string';

document.onreadystatechange = function () {
  if (document.readyState === 'interactive') {
    addArticleSearchClickListeners();
    addArticleCategoryClickListeners();

    const queryParams = queryString.parse(location.search);
    const categories = [].concat(queryParams.category);

    if (categories) {
      Array.from(categories).forEach(categoryParam => {
        const relatedCategoryElem = document.querySelector(`.avoindata-article-category-filter[data-tagid="${categoryParam}"]`);
        if (relatedCategoryElem) {
          relatedCategoryElem.classList.add('active');
        }
      })
    }
  }
}

function addArticleSearchClickListeners() {
  const searchButton = document.getElementById('avoindata-articles-search-btn');
  const searchInput = document.getElementById('avoindata-articles-search-input');
  searchButton.onclick = searchArticlesSubmit;
  searchInput.onkeydown = searchArticlesOnEnter;
}

function addArticleCategoryClickListeners() {
  const categoryListWrapper = document.getElementsByClassName('avoindata-article-category-filter-wrapper');
  if (categoryListWrapper[0]){
    const categoryFilters = categoryListWrapper[0].querySelectorAll('.avoindata-article-category-filter');
    Array.from(categoryFilters).forEach(element => {
      element.onclick = searchArticlesApplyFilter;
    });
  }
}

function searchArticlesOnEnter() {
  if (event.key === 'Enter') {
    searchArticlesSubmit();
  }
}

function searchArticlesApplyFilter(event) {
  if (event.target) {
    const targetElem = event.target;
    if (targetElem.classList.contains('active')) {
      targetElem.classList.remove('active');
    } else {
      targetElem.classList.add('active');
    }
  }
  searchArticlesSubmit();
}

function searchArticlesSubmit() {
  const searchInput = document.getElementById('avoindata-articles-search-input');
  const categoryFilterIds = [];
  const categoryFilters = document.querySelectorAll('.avoindata-article-category-filter.active');
  
  Array.from(categoryFilters).forEach(elem => {
    if (elem.dataset.tagid) {
      categoryFilterIds.push(elem.dataset.tagid);
    }
  })

  const queryParams = queryString.stringify({
    'search': searchInput.value,
    'category[]': categoryFilterIds
  });

  if (queryParams.length > 0) {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/articles?' + queryParams);
  } else {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/articles');
  }
}
