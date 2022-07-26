/**
 * @file
 */

'use strict';

(function ($, Drupal) {
  const openText = Drupal.t("Expand all"),
        closeText = Drupal.t("Close all");

  Drupal.behaviors.avoindataExpanderBehavior = {
    attach: function (context) {
      let togglerIndex = 0;
      $('.avoindata-expander', context).once('avoindataExpanderBehavior').each(function (index, element) {
        // Check if current expander should be considered as a group of expanders
        // In case of group, add toggler button before first expander
        if ($(element).next().hasClass('avoindata-expander') && !$(element).prev().hasClass('avoindata-expander')) {
          const $groupToggler = $('<a class="pull-right avoindata-expander-group-toggler" data-expanded="false">' + openText + '</a>');
          togglerIndex++;
          $groupToggler.on('click', toggleAllAvoindataExpanders);
          const $togglerWrapper = $('<div class="clearfix avoindata-expander-group-toggler-container"></div>').append($groupToggler);
          $togglerWrapper.insertBefore(element);
        }
        // Apply the avoindataExpanderBehavior effect to the elements only once.
        $('.avoindata-expander-header', this).on('click', toggleAvoindataExpander);
      });
    }
  };

  function toggleAvoindataExpander() {
    // Toggle status for current expander
    if ($(this.parentElement).hasClass('open')) {
      $('.icon-wrapper i', this.parentElement).removeClass('fa-angle-up').addClass('fa-angle-down');
      $(this.parentElement).removeClass('open');
    } else {
      $('.icon-wrapper i', this.parentElement).removeClass('fa-angle-down').addClass('fa-angle-up');
      $(this.parentElement).addClass('open');
    }

    // If next or previous element is also avoindata-expander, consider them as a group of expanders
    // and resolve a status for toggler
    const $container = $(this).closest('.avoindata-expander');
    if ($container.next().hasClass('avoindata-expander') || $container.prev().hasClass('avoindata-expander')) {
      let $togglerContainer = $container;
      // Find matching toggler for current expander group
      while (!$togglerContainer.hasClass('avoindata-expander-group-toggler-container')) {
        $togglerContainer = $togglerContainer.prev();
      }

      // Define helper variables to see if all expanders are closed or opened
      let allClosed = true;
      let allOpen = true;

      // Get first expander element in this group
      let $expander = $togglerContainer.next();

      // Loop through all expanders in this group
      while ($expander.hasClass('avoindata-expander')) {
        if ($expander.hasClass('open')) {
          allClosed = false;
        } else {
          allOpen = false;
        }
        $expander = $expander.next();
      }

      // Define status for toggler if all expanders in group have same state
      if (allOpen) {
        updateTogglerState($togglerContainer.find('.avoindata-expander-group-toggler'), true);
      } else if (allClosed) {
        updateTogglerState($togglerContainer.find('.avoindata-expander-group-toggler'), false);
      }
    }
  }

  function toggleAllAvoindataExpanders(event) {
    let $expander = $(event.currentTarget).parent().next();
    const currentlyExpanded = $(event.currentTarget).data('expanded');

    // Loop through all consecutive expanders
    while ($expander.hasClass('avoindata-expander')) {
      // If group is expanded when toggler was clicked, we should close all expander-elements in group
      if (currentlyExpanded) {
        $expander.removeClass('open');
        $expander.find('.icon-wrapper > i').addClass('fa-angle-down').removeClass('fa-angle-up');
      } else {
        $expander.addClass('open');
        $expander.find('.icon-wrapper > i').removeClass('fa-angle-down').addClass('fa-angle-up');
      }
      $expander = $expander.next();
    }

    // Use reversed currentState as state is now changed for all expanders in group
    updateTogglerState($(event.currentTarget), !currentlyExpanded);
  }

  /**
   * Defines text and state for toggler
   * @param {Jquery object} $toggler
   * @param {boolean} expand New state of toggler
   */
  function updateTogglerState($toggler, expand) {
    $toggler.text(expand ? closeText : openText);
    $toggler.data('expanded', expand);
  }

  Drupal.behaviors.guideMenuListener = {
    attach: function (context) {
      $('#guide-menu-column .nav__item.open .subnav', context).each(guideMenuInit);
    }
  }

  /**
   * Initializes interaction between guide menu and content
   */
  function guideMenuInit(index, subnavElement) {
    // Make nav-item activation working also by scroll position
    guideMenuListenScroll(subnavElement);
  }

  function guideMenuListenScroll(subnavElement) {
    const $sections = $('.avoindata-section');
    // Init trigger position on top of window
    const triggerPosition = 0;
    // Only add scroll listener when there is sections in page
    if ($sections.length > 0) {
      $('body').on('scroll', function () {
        for (let i = 0; i < $sections.length; i++) {
          const section = $sections[i];
          const offsetTop = $(section).offset().top - parseInt($(section).css('marginTop'));
          const offsetTopSectionBottom = offsetTop + $(section).outerHeight();

          // As long as section is visible in screen, set it active in menu
          if (offsetTop < triggerPosition  && triggerPosition <= offsetTopSectionBottom) {
            let hash = '#' + $(section).attr('id');
            guideMenuSetActiveSubnavItemByHash(subnavElement, hash);
            break;
          }
        }
      });
    }
  }

  /**
   * Sets active item in menu by given hash
   */
  function guideMenuSetActiveSubnavItemByHash(subnavElement, hash) {
    $('.nav__item__link.active--subnav-link', subnavElement).removeClass('active--subnav-link');
    $('a[href="' + hash + '"]', subnavElement).addClass('active--subnav-link');
    var url = new URL(window.location);
    url.hash = hash;

    if (window.location.hash !== hash) {
      history.replaceState({}, "", url);
    }
  }
})(jQuery, Drupal);
