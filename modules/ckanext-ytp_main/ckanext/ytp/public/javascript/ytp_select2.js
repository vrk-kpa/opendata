$(window).on("load", function() {
  //$(".select2-container").after('<ul class="select2-tags-container"></ul>')

  $('input[data-module="autocomplete"]')
    .on("change", function(e) {
      var $tag = e.added ? e.added : e.removed ? e.removed : "";
      $tag.container = this.id;
      var $container = $(this).siblings(".ytp-select2-tags-container");
      if (!$container || $container.length === 0) {
        $(this).after('<div class="ytp-select2-tags-container"></div>');
        $container = $(this).siblings(".ytp-select2-tags-container");
      }

      if (e.added) {
        $container.append(`
          <span class="avoindata-pill badge badge-pill" data-tag-id="${$tag.id}" data-container-id="${$tag.container}">
            <span class="truncate-text">${$tag.text}</span>
            <i class="fal fa-times"></i>
          </span>`);
          console.log($(this)
          .siblings(".ytp-select2-tags-container").find('span:last-child'));
        $(this)
          .siblings(".ytp-select2-tags-container").find('span:last-child')
          .on("click", function(e) {
            // container is the clicked custom tag (pill/badge/chip/whatever) below the select2 field
            var container = $(e.target).hasClass('avoindata-pill') ? $(e.target) : $(e.target).parents('.avoindata-pill');

            // contains the list of select2 (the data of the original hidden select2 tags)
            var data = $('#' + container.data().containerId).select2("data");

            // filter out the removed tag from the original hidden select2 tags
            $('#' + container.data().containerId).select2("data", data.filter(pill => pill.id != container.data().tagId));

            // remove the custom tag as well after it's removed from the select2 tags
            container.remove();
          });
      }
    })
    .trigger("change");
});
