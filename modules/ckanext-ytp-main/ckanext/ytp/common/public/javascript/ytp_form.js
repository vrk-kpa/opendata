
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
