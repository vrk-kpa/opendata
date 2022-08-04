$(window).on("load", function() {
  $('input[data-module="autocomplete"]').each(function(index, element) {
    if (element.value.length > 0 && element.value.split(',').length > 0) {
      element.value.split(',')
        .forEach(function(tag) {
          tag = { container: element.id, id: tag, text: tag};
          var container = $(element).siblings(".ytp-select2-tags-container");

          if (!container || container.length === 0) {
            $(element).after('<div class="ytp-select2-tags-container"></div>');
            container = $(element).siblings(".ytp-select2-tags-container");
          }

          createTag(tag, container);
        });
    }
  });

  $('select[data-module="autocomplete"].ytp-badges').each(function(index, element) {
    if (element.selectedOptions.length > 0) {
      for (var i = 0; i < element.selectedOptions.length; i++) {
          var tag = element.selectedOptions[i];
          tag = { container: element.id, id: tag.label, text: tag.label};
          var container = $(element).siblings(".ytp-select2-tags-container");

          if (!container || container.length === 0) {
            $(element).after('<div class="ytp-select2-tags-container"></div>');
            container = $(element).siblings(".ytp-select2-tags-container");
          }

          createTag(tag, container);
        }
    }
  });

  $('input[data-module="autocomplete"]')
    .on("change", function(e) {
      if (e.added) {
        var tag = e.added;
        tag.container = this.id;
        var container = $(this).siblings(".ytp-select2-tags-container");

        if (!container || container.length === 0) {
          $(this).after('<div class="ytp-select2-tags-container"></div>');
          container = $(this).siblings(".ytp-select2-tags-container");
        }

        createTag(tag, container);

        // single select components remove previous element, eg format selector
        if (e.removed ){
          removeTag(e.removed, container);
        }
      }
    });

    $('select[data-module="autocomplete"].ytp-badges')
    .on("change", function(e) {
      if (e.added) {
        var tag = e.added;
        tag.container = this.id;
        var container = $(this).siblings(".ytp-select2-tags-container");

        if (!container || container.length === 0) {
          $(this).after('<div class="ytp-select2-tags-container"></div>');
          container = $(this).siblings(".ytp-select2-tags-container");
        }

        createTag(tag, container);
      }
    });
});

var createTag = function(tag, container) {
  container.append(`
    <span class="avoindata-pill badge badge-pill" data-tag-id="${tag.id}" data-container-id="${tag.container}">
      <span class="truncate-text">${escapeHTML(tag.text)}</span>
      <i class="fal fa-times"></i>
    </span>`);

  container.find("span:last-child").on("click", function(e) {
    // badge is the clicked custom tag (pill/badge/chip/whatever) below the select2 field
    var badge = $(e.target).hasClass("avoindata-pill")
      ? $(e.target)
      : $(e.target).parents(".avoindata-pill");

    // contains the list of select2 (the data of the original hidden select2 tags)
    var data = $("#" + badge.data().containerId).select2("data");

    // multi-select is array, single-select is object
    if (Array.isArray(data)) {

      // filter out the removed tag from the original hidden select2 tags
      $("#" + badge.data().containerId).select2(
        "data",
        data.filter(pill => pill.text != badge.data().tagId)
      );
    }

    else {
      // set single-select value to null to make it empty
      $("#" + badge.data().containerId).select2(
        "data",
        null
      );
    }

    // remove the custom tag as well after it's removed from the select2 tags
    badge.remove();
  });
};

let removeTag = function(tag, container) {
  container.find(`[data-tag-id="${tag.id}"]`).remove();
};

let escapeHTML = (html) => {
  let escape = document.createElement('textarea');
  escape.textContent = html;
  return escape.innerHTML;
}
