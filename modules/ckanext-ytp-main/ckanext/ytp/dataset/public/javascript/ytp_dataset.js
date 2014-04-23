
function show_languages(locales, locales_disabled) {
    $.each(locales, function(index, locale) {
        $("[translation-data-locale='" + locale + "']").show();
    });
    $.each(locales_disabled, function(index, locale) {
        $("[translation-data-locale='" + locale + "']").hide();
        $("input[translation-data-locale='" + locale + "']").val("");
        $("textarea[translation-data-locale='" + locale + "']").val("");
    });

    $('.translation-list').each(function() {
       var container = $(this);
       var visible_inputs = container.find('.translation-input:visible');
       var size_persent = (100.0 - visible_inputs.length) / visible_inputs.length;
       if (visible_inputs.length == 1) {
           size_persent = 100;
       }
       visible_inputs.closest('.translation-container').css('width', size_persent.toString() + "%");
    });
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
