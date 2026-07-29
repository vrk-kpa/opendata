/**
 * @file
 */

document.addEventListener('readystatechange', event => {
  if (event.target.readyState === 'interactive') {
    addArticleSearchClickListeners();
    addArticleCategoryClickListeners();

    const queryParams = new URLSearchParams(location.search);
    const categories = queryParams.getAll('category');

    if (categories) {
      categories.forEach(categoryParam => {
        const relatedCategoryElem = document.querySelector(`.avoindata - article - category - filter[data - tagid = "${categoryParam}"]`);
        if (relatedCategoryElem) {
          relatedCategoryElem.classList.add('active');
        }
      })
    }
  }
});

function addArticleSearchClickListeners() {
  const searchButton = document.getElementById('avoindata-articles-search-btn');
  const searchInput = document.getElementById('avoindata-articles-search-input');
  searchButton.onclick = searchArticlesSubmit;
  searchInput.onkeydown = searchArticlesOnEnter;
}

function addArticleCategoryClickListeners() {
  const categoryListWrapper = document.getElementsByClassName('avoindata-article-category-filter-wrapper');
  if (categoryListWrapper[0]) {
    const categoryFilters = categoryListWrapper[0].querySelectorAll('.avoindata-article-category-filter');
    Array.from(categoryFilters).forEach(element => {
      element.onclick = searchArticlesApplyFilter;
    });
  }
}

function searchArticlesOnEnter(event) {
  if (event.key === 'Enter') {
    searchArticlesSubmit();
  }
}

function searchArticlesApplyFilter(event) {
  if (event.target) {
    const targetElem = event.target;
    if (targetElem.classList.contains('active')) {
      targetElem.classList.remove('active');
    }
else {
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

  const searchParams = new URLSearchParams();
  searchParams.append('search', searchInput.value);
  categoryFilterIds.forEach(c => searchParams.append('category[]', c));
  const queryParams = searchParams.toString();

  if (queryParams.length > 0) {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/articles?' + queryParams);
  }
else {
    window.location.replace(window.location.origin + '/' + searchInput.dataset.searchLanguage + '/articles');
  }
}
