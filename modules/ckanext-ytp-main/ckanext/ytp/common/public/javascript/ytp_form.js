/**
 * 
 * @param inputContainer A div container element which includes an input field
 */
function createRemoveLink(inputContainer) {
    // The remove link with the icon
    var removeLink = $('<a href="javascript:void(0);" class="ytp-add-input"><span class="icon-minus-sign-alt icon-2x"></span></a>');
    // Add an event listener for removing the input field container
    removeLink.click(function() {
        // Remove the value inside the container's input field
        inputContainer.find('> input').val("");
        // Remove the container
        inputContainer.remove();
        return false;
    });
    // Append the remove link to the input container
    inputContainer.append(removeLink);
    return removeLink;
}

$(document).ready(function() {
    /* Create an add link for all the ytp-multiple-values child div elements. The add link clones the input container. */
    $('.ytp-multiple-values').each(function() {
        var listContainer = $(this);
        // Loop through all the children divs inside ytp-multiple-values
        listContainer.children('div').each(function(valueIndex) {
            if (valueIndex == 0) {
                // We are adding the 'add link' only to the first child
                var addLink = $('<a href="javascript:void(0);" class="ytp-add-input"><span class="icon-plus-sign-alt icon-2x"></span></a>');
                var inputContainer = $(this);
                inputContainer.append(addLink);

                addLink.click(function() {
                    // Clone the input container div which contains the input field
                    var clonedInputContainer = inputContainer.clone();
                    // Clear the input field's value and remove the id
                    clonedInputContainer.find('> input').val("").removeAttr('id');
                    // Remove the 'add link' button from the input container
                    clonedInputContainer.find('> a').remove();
                    // Append the cloned input container after the last element
                    listContainer.append(clonedInputContainer);
                    // Add the 'remove link' to the cloned input container
                    createRemoveLink(clonedInputContainer);
                    return false;
                });
            } else {
                // We are adding the remove link to all the other children
                createRemoveLink($(this));
            }
        });
    });

    $('.submit-on-change').change(function() {
        this.form.submit();
    });
});


function show_languages(locales, locales_disabled) {
    $.each(locales, function(index, locale) {
        $("[translation-data-locale='" + locale + "']").show();
    });
    $.each(locales_disabled, function(index, locale) {
        $("[translation-data-locale='" + locale + "']").hide();
        $("input[translation-data-locale='" + locale + "']").val("");
        $("textarea[translation-data-locale='" + locale + "']").val("");
    });

    var visibleCount = $('[name=translations]:checked').length + 1;

    var sizePersent = (100.0 - visibleCount) / visibleCount;
    if (visibleCount == 1) {
        sizePersent = 100;
    }

    if (visibleCount == 1) {
        // If only one language has been selected, set the width of the input field to match the width of the non-translateable fields
        $('.control-medium .translation-container').css('width', "320px");
        // In any case, set the text area width to be as wide as possible
        $('.control-full .translation-container').css('width', sizePersent.toString() + "%");
    } else {
        // If more than one language has been selected, set the width according to the number of fields
        $('.translation-container').css('width', sizePersent.toString() + "%");
    }
}

function set_translations() {
    $('.language').hide();

    $('.translation-select:checked').each(function(index, element) {
        if (!$(element).attr('disabled')) {
            $('#translate_' + $(element).val()).css('display', 'inline-block');
        }
    });
    var locales = [];
    var locales_disabled = [];

    $('.translation-select').each(function(index, element) {
        var element = $(element);
        var locale = element.val();
        if (element.prop('checked')) { 
            locales.push(locale);
        } else {
            locales_disabled.push(locale);
        }
    });

    show_languages(locales, locales_disabled);
}

function set_original_language() {
    var language_code = $('.translation-select-original:checked').val();
    $('.translate-original-language').html($('#translate_' + language_code).text());
    $('.translation-select').removeAttr('disabled');
    $('#translation_select_' + language_code).removeAttr('checked').attr('disabled', 'disabled');
    $('.translation-input-original').text(language_code);
    set_translations();
}

function modal_confirm(modal_id, ok_method, cancel_method) {
    var modal = $('#' + modal_id);
    $('#' + modal_id + "_cancel").click(function() {
       cancel_method();
       modal.hide(); 
    });
    $('#' + modal_id + "_dismiss").click(function() {
       cancel_method();
       modal.hide(); 
    });
    $('#' + modal_id + "_ok").click(function() {
       ok_method();
       modal.hide(); 
    });
    modal.show();
}

/* Create add link for all ytp-list class elements. Add link clones the input. */
$(document).ready(function() {
    var previous_original_language = $('.translation-select-original:checked');
    $('.translate-language-show').click(function() {
        $('.translate-language-select').slideToggle();
    });

    $('.translation-select-original').change(function() {
        if (previous_original_language.length == 1 && $("#translation_select_" + $(this).val()).prop('checked')) {
            modal_confirm("modal_confirm_original", set_original_language, function() {
                $('.translation-select-original:checked').removeAttr('checked');
                $('.translation-select-original[value="' + previous_original_language.val() + '"]').prop('checked', 'checked');
            });
            return;
        }
        set_original_language();
        previous_original_language = $('.translation-select-original:checked');
    });
    $('.translation-select-original:checked').each(set_original_language);

    $('.translation-select').change(function() {
        if (!$(this).prop('checked')) {
            var element = $(this); 
            modal_confirm("modal_confirm_translation", set_translations, function() {
                element.prop('checked', 'checked');
            });
            return;
        }
        set_translations();
    });

    if ($('.translation-select-original:checked').length === 0) {
        $('.translation-select').removeAttr('checked').attr('disabled', 'disabled');
    }

    set_translations();
});

/**
 * Sets the visibility of the target element's closest element with the given parentClass depending on the given element and data
 * 
 * @param target The target element
 * @param parentClass The class for identifying the closest parent element of the target element whose visibility is changed
 * @param element The name of the element based on which the visibility is changed
 * @param data The value of the element based on which the visibility is changed
 */
function setTargetVisibility(target, parentClass, element, data) {
    var targetContainer = target.closest(parentClass);
    if ($('[name=' + element + ']:checked').val() == data) {
        targetContainer.show();
    } else {
        targetContainer.hide();
        target.val('');
    }
}

$(document).ready(function() {
     $('[data-ytp-visible-element]').each(function() {
         var target = $(this);
         var element = target.attr('data-ytp-visible-element');
         var data = target.attr('data-ytp-visible-data');
         var parentClass = '.control-group';
         setTargetVisibility(target, parentClass, element, data);
         $('[name=' + element + ']').change(function() {
             setTargetVisibility(target, parentClass, element, data);
         });
     });
});

$(document).ready(function() {
    /* Loop through all elements with the data-ytp-visible-after-element attribute */
    $('[data-ytp-visible-after-element]').each(function() {
        var target = $(this);

        // All the input fields inside the translation-list contain the data-ytp-visible-after-element attribute. We're only interested to perform the
        // statements inside the if statement for one of those fields. Since all the localized fields have the translation-data-locale attribute, we can
        // target the original input field by checking that the field does not have the translation-data-locale attribute.
        if (!target.attr('translation-data-locale')) {
            var element = target.attr('data-ytp-visible-after-element');
            var data = target.attr('data-ytp-visible-after-data');
            // We want to show/hide the div with the translation-list class
            var parentClass = '.translation-list';

            // Get the element which has the translation-list class
            var targetTranslationContainer = target.closest(parentClass);
            targetTranslationContainer.css('margin-top', '15px');

            // Get the element after which we will move the translation-list
            var elementContainer = $('[name=' + element + '][value=' + data + ']').closest('.radio-select-label');
            // Remove the parent div with the control-group class since we are going to move the translation-list from within it to another location
            target.closest('.control-group').remove();
            // Move the translation-list after the radio-select-label with the given name and value
            elementContainer.after(targetTranslationContainer);

            // Set the visibility of the translation-list
            setTargetVisibility(targetTranslationContainer, parentClass, element, data);
            $('[name=' + element + ']').change(function() {
                // Bind the field group to set the visibility of the translation-list upon change
                setTargetVisibility(targetTranslationContainer, parentClass, element, data);
            });
       }
    });
});


$(document).ready(function(){
    $('[data-datepicker]').each(function() {
        $(this).datetimepicker({
            pickTime: false
        });
    })

    $('[data-tree]').each(function(){
        var TreeConfig = JSON.parse($(this).attr('attrs'));
        if ($.isEmptyObject(TreeConfig)) {
            $(this).jstree({
                plugins: ['checkbox']
            });
        }
        else{
            $(this).jstree(TreeConfig);
        }
    })
});


/**
 * 
 * @param tree A jsTree instance
 * @param nodesToSelect A string indicating which nodes to select ('all', 'top', 'bottom')
 * @param targetElementId The id of the target input field
 */
function transferSelectedFromTreeToForm(tree, nodesToSelect, targetElementId) {
    // Check whether we are selecting all the nodes, just the parents, or just the children
    if (!nodesToSelect || nodesToSelect == "all") {
        var selected = tree.get_selected('full');
    } else if (nodesToSelect == "top") {
        selected = tree.get_top_selected('full');
    } else if (nodesToSelect == "bottom") {
        selected = tree.get_bottom_selected('full');
    }

    // Get a reference to the input field we are updating
    var input = $('#' + targetElementId);
    // Get the array of values in the input field
    var values = input.select2('data');
    // Empty the array
    values.length = 0;

    selected.forEach(function(element) {
        // Append each of the selected items to the array
        values.push({id: tree.get_text(element), text: tree.get_text(element), locked: true});
    });

    // Update the input field's values
    input.select2('data', values);
}