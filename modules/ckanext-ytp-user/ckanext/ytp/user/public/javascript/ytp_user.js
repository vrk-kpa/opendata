
$(document).ready(function() {
    $('.ytp-list').each(function(){
        /* Create add link for all ytp-list class elements. Add link clones the input. */
        var add_link = $('<a href="#" class="ytp-add-input" style="margin-left: 3px;"><i class="icon-plus-sign-alt icon-large"></i></a>');
        var input = $(this);
        var index = 0;
        add_link.click(function() {
            add_link.before(input.clone().val("").attr('id', input.attr('id') + "-clone-" + (++index)));
        });
        input.after(add_link);
    });

    $('.submit-on-change').change(function() {
        this.form.submit();
    });
});
