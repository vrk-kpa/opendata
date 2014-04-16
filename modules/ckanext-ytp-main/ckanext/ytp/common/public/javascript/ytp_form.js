
$(document).ready(function() {
    $('.ytp-list').each(function(){
        /* Create add link for all ytp-list class elements. Add link clones the input. */
        var addLink = $('<a href="javascript:void(0);" class="ytp-add-input" style="margin-left: 3px;"><i class="icon-plus-sign-alt icon-large"></i></a>');
        var input = $(this);
        var index = 0;
        addLink.click(function() {
            var cloned = input.clone().val("").attr('id', input.attr('id') + "-clone-" + (++index));
            addLink.after(cloned);
            var removeLink = $('<a href="javascript:void(0);" class="ytp-add-input" style="margin-left: 3px;"><i class="icon-minus-sign-alt icon-large"></i></a>');
            cloned.after(removeLink);
            removeLink.click(function() {
                cloned.val("").remove();
                removeLink.remove();
                return false;
            });
            return false;
        });
        input.after(addLink);
    });

    $('.submit-on-change').change(function() {
        this.form.submit();
    });
});
