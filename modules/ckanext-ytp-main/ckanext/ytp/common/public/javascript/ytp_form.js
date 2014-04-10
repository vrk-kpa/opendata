
$(document).ready(function() {
    $('.ytp-list').each(function(){
        /* Create add link for all ytp-list class elements. Add link clones the input. */
        var addLink = $('<a href="#" class="ytp-add-input" style="margin-left: 3px;"><i class="icon-plus-sign-alt icon-large"></i></a>');
        var input = $(this);
        var index = 0;
        addLink.click(function() {
            addLink.before(input.clone().val("").attr('id', input.attr('id') + "-clone-" + (++index)));
            return false;
        });
        input.after(addLink);
    });

    $('.submit-on-change').change(function() {
        this.form.submit();
    });
});
