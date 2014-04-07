
function rename_input() {
    var value = $(this).val();
    $(this).parent().find('input, textarea').each(function(element_index, element) {
        var input = $(element);
        var split = input.attr('name').split("_");
        input.attr('name', split.slice(0, split.length - 1).join("_") + "_" + value);
    });
}

/* Create add link for all ytp-list class elements. Add link clones the input. */
$(document).ready(function() {
    $('.ytp-locale-list').each(function(){
        var add_link = $('<a href="#" class="ytp-add-input" style="margin-left: 3px; position: absolute; right: -10em; top: 10px;"><i class="icon-plus-sign-alt icon-large"></i></a>');
        var container = $(this);
        var index = 0;

        add_link.click(function() {
            var new_container = container.clone();
            index += 1;

            var locale_select = new_container.find('.locale-select');
            locale_select.attr('name', locale_select.attr('name') + "-" + index);

            new_container.find('input, textarea').each(function(element_index, element) {
                var input = $(element);
                input.attr('data-module', '').val("").attr('id', input.attr('id') + "-clone-" + index);
                input.data('name', input.attr('name'));
                input.attr('name', input.attr('name') + "_" + new_container.find('.locale-select').val());
            });

            new_container.find('.locale-select').change(rename_input);

            new_container.find('.slug-preview').remove();
            add_link.before(new_container);

            return false;
        });
        $(this).after(add_link);
    });
    $('.locale-select-change').change(rename_input);

});
