
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
    serviceSetupNavigationButtons(currentPhase);
});
