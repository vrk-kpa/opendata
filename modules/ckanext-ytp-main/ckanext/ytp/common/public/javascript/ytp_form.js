
function createRemoveLink(item) {
    var removeLink = $('<a href="javascript:void(0);" class="ytp-add-input" style="margin-left: 3px;"><i class="icon-minus-sign-alt icon-large"></i></a>');
    removeLink.click(function() {
        item.val("").remove();
        removeLink.remove();
        return false;
    });
    item.after(removeLink);
    return removeLink;
}

$(document).ready(function() {
    /* Create add link for all ytp-list class elements. Add link clones the input. */
    $('.ytp-multiple-values').each(function() {
        var container = $(this);
        container.find('.ytp-multiple-value').each(function(valueIndex) {
            if (valueIndex == 0) {
                var addLink = $('<a href="javascript:void(0);" class="ytp-add-input" style="margin-left: 3px;"><i class="icon-plus-sign-alt icon-large"></i></a>');
                var input = $(this);

                addLink.click(function() {
                    var cloned = input.clone().val("").removeAttr('id');
                    container.append(cloned);
                    createRemoveLink(cloned);
                    return false;
                });
                input.after(addLink);
            } else {
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

    $('.translation-container').css('width', sizePersent.toString() + "%");
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

