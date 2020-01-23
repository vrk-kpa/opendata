$(document).ready(function() {
  $("[data-datepicker]").each(function() {
    $(this).datetimepicker({
      format: "YYYY-MM-DD"
    });
  });

  $("[data-datetimepicker]").each(function() {
    $(this).datetimepicker({
      format: "YYYY-MM-DD HH:mm:ss"
    });
  });

  $("#submit-showcase-form").submit(function(event) {
    event.preventDefault();
    grecaptcha.reset();
    grecaptcha.execute();
  });
});

// Calculate file size on resource submit.
$(function() {
  $("#resource-edit").one("submit", function() {
    var fileInput = $("#resource-edit input:file").get(0);
    if (fileInput.files.length > 0) {
      var fileSize = fileInput.files[0].size;
      $("#field-size").val(fileSize);
      var html = $(
        '<div class="upload-times"><ul>' +
          "<li>24/1 Mbit/s: " +
          Math.ceil(fileSize / 125000 / 60) +
          " min</li>" +
          "<li>10/10 Mbit/s: " +
          Math.ceil(fileSize / 1250000 / 60) +
          " min</li>" +
          "<li>100/100 Mbit/s: " +
          Math.ceil(fileSize / 12500000 / 60) +
          " min</li>" +
          "</ul></div>"
      );

      $("#submit-info")
        .append(html)
        .show();
    }
  });
});

ckan.module("ytp_main_input_multiple", function($) {
  return {
    initialize: function() {
      var module = this;
      var addLinkText = module._("Add link");
      $(function() {
        /* Create an add link for all the multiple-values child div elements. The add link clones the input container. */
        $(".multiple-values").each(function(index, element) {
          var listContainer = $(element);

          if (listContainer.siblings('button.add-input-button').length > 0) {
              return false;
          }
          // We are adding the 'add link' after the listContainer
          var addLink = $(
            '<button type="button" class="add-input-button"><i class="fa fa-globe"></i>' +
              addLinkText +
              "</button>"
          );

          addLink.click(function(e) {
            var inputContainer = $(element)
              .children("div")
              .first();
            // Clone the input container div which contains the input field
            var clonedInputContainer = inputContainer.clone();
            // Clear the input field's value and remove the id
            clonedInputContainer
              .find("> input")
              .val("")
              .removeAttr("id")
              .removeAttr("data-module");

            clonedInputContainer.addClass("removable-input-container");

            // Append the cloned input container after the last element
            listContainer.append(clonedInputContainer);

            // Add the 'remove link' to the cloned input container
            module.createRemoveLink(clonedInputContainer);
            e.stopPropagation();
            e.preventDefault();
            return false;
          });

          listContainer.after(addLink);

          if ($(element).children("div").length > 1) {
            $(element).children("div").each(function(subIndex, subElement) {
                if (subIndex > 0) {
                    // Add the 'remove link' to all input containers except the first
                    $(subElement).addClass("removable-input-container");
                    module.createRemoveLink($(subElement));
                }
            });
          }
        });
      });
    },
    createRemoveLink: function(inputContainer) {
      var removeLinkText = this._("Remove");
      // The remove link with the icon
      var removeLink = $(
        '<button type="button" class="remove-input-button"><i class="far fa-trash"></i>' +
          removeLinkText +
          "</button>"
      );
      // Add an event listener for removing the input field container
      removeLink.click(function(e) {
        // Remove the value inside the container's input field
        inputContainer.find("> input").val("");
        // Remove the container
        inputContainer.remove();
        e.stopPropagation();
        e.preventDefault();
        return false;
      });
      // Append the remove link to the input container
      inputContainer.append(removeLink);
      return removeLink;
    }
  };
});
