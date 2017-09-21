$(document).ready(function(){
    /* Create an add link for all the multiple-values child div elements. The add link clones the input container. */
    $('.multiple-values').each(function() {
        var listContainer = $(this);
        // Loop through all the children divs inside multiple-values
        listContainer.children('div').each(function(valueIndex) {
            if (valueIndex == 0) {
                // We are adding the 'add link' only to the first child
                var addLink = $('<a href="javascript:void(0);" class="add-input"><span class="icon-plus-sign-alt icon-2x"></span></a>');
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

});

function createRemoveLink(inputContainer) {
    // The remove link with the icon
    var removeLink = $('<a href="javascript:void(0);" class="add-input"><span class="icon-minus-sign-alt icon-2x"></span></a>');
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