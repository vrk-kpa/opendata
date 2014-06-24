

function serviceShowPhase(tabs, name) {
    var current = $('[data-service-tabs=' + tabs + ']');
    var content = $('[data-service-contents=' + tabs + ']');

    content.children('[data-service-content]').hide();
    content.children('[data-service-content=' +  name + ']').show();

    var allTabs = current.children('[data-service-tab]');

    allTabs.removeClass('active');
    activeTab = current.children('[data-service-tab=' +  name + ']');
    activeTab.addClass('active');

    serviceSetupNavigationButtons(allTabs.index(activeTab) + 1);
}

function serviceSetupNavigationButtons(index) {
    if (index <= 1) {
        $('.service-previous-phase').hide();
        $('.service-next-phase').show();
    } else if (index >= 4) {
        $('.service-next-phase').hide();
        $('.service-previous-phase').show();
    } else {
        $('.service-next-phase').show();
        $('.service-previous-phase').show();
    }
}

$(document).ready(function() {
    var currentPhase = 1;
    var serviceChannelIndex = $('#free_resource_index').val();
    if (!serviceChannelIndex) {
        serviceChannelIndex = 0;
    }

    $('.service-next-phase').click(function() {
        var next = $('[data-service-tabs="services"]').find('.active').first().next();
        if (next.length == 0) {
            return false;
        }
        serviceShowPhase("services", next.attr('data-service-tab'));
        serviceSetupNavigationButtons(++currentPhase);
        return false;
    });

    $('.service-previous-phase').click(function() {
        var previous = $('[data-service-tabs="services"]').find('.active').first().prev();
        if (previous.length == 0) {
            return false;
        }
        serviceShowPhase("services", previous.attr('data-service-tab'));
        serviceSetupNavigationButtons(--currentPhase);
        return false;
    });

    $('[data-service-tabs]').each(function() {
        var current = $(this);
        var tabs = current.attr('data-service-tabs');
        current.find('[data-service-tab]').click(function() {
            serviceShowPhase(tabs, $(this).attr('data-service-tab'));
        });
        serviceShowPhase(tabs, current.find('.active').first().attr('data-service-tab'));
    });

    $('.service-channels-add').click(function() {
        var currentIndex = serviceChannelIndex;
        serviceChannelIndex++;

        var element = $(this).attr('data-service-channels-element');
        if (!element) {
            alert("Error: Failed to add data");
            return false;
        }
        var source = $("[data-service-content=" + element + "]");
        var clonedData = source.clone();

        clonedData.attr('data-service-content', '');

        clonedData.find('[id]').each(function() {
            var element = $(this);
            element.attr('id', element.attr('id') + "_" + currentIndex);
        });

        clonedData.find('[name]').each(function() {
            var element = $(this);
            var element_name = element.attr('name');
            element.attr('name', "resources__" + currentIndex + "__" + element_name);
        });

        clonedData.find("button").remove();

        clonedData.hide();

        var container = $('<li class="service-channels-item" id="resource_' + currentIndex + '"></li>').appendTo('#service-channels-list');
        var link = $('<a href="javascript:void(0);"></a>');
        var removeLink = $("#service-channel-remove-template").clone();
        removeLink.show();
        link.appendTo(container).append('<i class="icon-plus"></i> ' + $('[data-service-tab=' + element + ']').text());
        removeLink.appendTo(container);

        container.append(clonedData);

        removeLink.click(function() {
            if (confirm(removeLink.attr('data-confirm-message'))) {
                container.remove();
            }
            return false;
        });

        link.click(function() {
            clonedData.toggle();
            return false;
        });
        source.find('[name]').each(function(index, input) {
            input = $(input);
            var name = input.attr('name');
            if (name == 'url' || name == 'service_channel_type') {
                return;
            }
            input.val('');
        });

        return false;
    });

    serviceSetupNavigationButtons(currentPhase);

});
