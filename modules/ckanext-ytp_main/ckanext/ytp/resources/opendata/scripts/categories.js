var Categories = {
    init: function() {
        var self = this;
        $(function () {
            // Listen for more categories-button
            var toggleButton = document.querySelector('#show-more-categories');
            if (toggleButton) {
                toggleButton.addEventListener('click', function() {
                    self.toggleCategories(toggleButton);
                });
            }
        });
    },
    toggleCategories: function(toggleButton) {
        var hiddenCategories = toggleButton.parentNode.parentNode.querySelectorAll('.categories__list__item--hidden')

        if (hiddenCategories) {
            hiddenCategories.forEach(function(categoryElement) {
                categoryElement.classList.remove('categories__list__item--hidden');
            });
        }
        toggleButton.remove();
    }
}

Categories.init();
