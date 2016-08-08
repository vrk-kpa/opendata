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
        //$("[data-translation-locale='" + locale + "']").show();
        $('[data-translation-locale="' + locale + '"][data-translation-hidden]').removeAttr('data-translation-hidden');
    });
    $.each(locales_disabled, function(index, locale) {
        $("[data-translation-locale='" + locale + "']").attr('data-translation-hidden', '');
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
        $('.control-medium .translation-container').css('width', "440px");
        // In any case, set the text area width to be as wide as possible
        //$('.control-full .translation-container').css('width', sizePersent.toString() + "%");
        $('.control-full .translation-container').removeClass('col-sm-4 col-sm-6').addClass('col-sm-12');
    } else if (visibleCount == 2){
        $('.control-full .translation-container').removeClass('col-sm-4').addClass('col-sm-6');
    } else if (visibleCount == 3) {
        $('.control-full .translation-container').addClass('col-sm-4');
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

    var input_element = $('[data-translation-original]');
    if (input_element.parent().hasClass('input-group')){
        input_element.siblings('span').attr('data-translation-original', language_code).text(language_code);
    }
    else {
        var language_element = $('<div class="input-group"></div>');
        input_element.wrap(language_element).before('<span data-translation-original=' + language_code + ' class="translation-input-language input-group-addon">' + language_code + '</span>');
    }
    //$('.translation-input-original').text(language_code);
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
    //$('.translate-language-show').click(function() {
    //    $('.translate-language-select').slideToggle();
    //});

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

function toggleClass(classToToggle) {
    $('.' + classToToggle).toggle();
}

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
    });

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
    });

    $('[data-organization-tree] .js-expand').bind('click', function(){
        $(this).siblings('.js-collapse, .js-collapsed').show();
        $(this).hide();
    });

    $('[data-organization-tree] .js-collapse').bind('click', function(){
        $(this).hide().siblings('.js-collapsed').hide();
        $(this).siblings('.js-expand').show();
    });

    $('[data-organization-filter]').bind('keyup cut paste', function(){
        var search_str = $(this).val().toLowerCase();

        if (search_str.length != 0){
            $('.js-collapse, .js-expand').hide();
            $('.js-collapsed').show();
            var organizations = $('.organization-row');
            organizations.hide();
            var count = 0;
            organizations.filter(function(index, element){
                return element.textContent.toLowerCase().indexOf(search_str) >= 0
            }).each(function(index, element){
                var text = $(element).find('a').get(0).textContent;
                var str_index = text.toLowerCase().indexOf(search_str);
                if ( str_index >= 0){
                    count++;
                    $(this).find('a').html(text.substr(0, str_index) + '<span class="highlight">' + text.substr(str_index, search_str.length) + '</span>' + text.substr(str_index + search_str.length))[0];
                }
            }).show();
        }
        else{
            count = $('.organization-row').length;
            $('span.highlight').contents().unwrap()
            $('.organization-row').show();
            $('.js-collapsed').hide();
            $('.js-expand').show();
        }

        var count_str = $('.search-form h1').text();
        var replaced = count_str.replace(/\d+/g, count);
        $('.search-form h1').text(replaced);
    })
});

$(document).ready(function(){
    $('.dropdown-toggle').dropdown();
    $('.tooltip-element span').tooltip();
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