// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module("ytp-multiselect", function($) {
  return {
    initialize: function() {
      let changes = false;

      $.proxyAll(this, /_on/);
      $.proxyAll(this, /_make/);
      $.proxy(this, /checkboxes/);

      // Collapse all multiselect dropdowns when clicking anywhere except within the current multiselect dropdown
      $(document).click(function(e) {
        // Check if click was triggered on or within .ytp-multiselect element
        if ($(e.target).closest(".ytp-multiselect").length > 0) {
          return;
        }

        // Otherwise
        // collapse all expanded multiselect dropdowns
        $(".ytp-multiselect.expanded").removeClass("expanded");
        if (changes) {
          $(".advanced-search-form").submit();
        }
      });

      // Add dropdown toggle event to main button
      this.el
        .find(".ytp-multiselect-toggle")
        .on("click", (e) => {
          if (this.el.hasClass("expanded")) {
            $(".ytp-multiselect.expanded").removeClass("expanded");
            this.el.addClass("expanded");
          } else {
            $(".ytp-multiselect.expanded").removeClass("expanded");
          }
          if (changes) {
            $(".advanced-search-form").submit();
          }
          this._onToggleMultiSelect(this.el);
        });


      // Find all inputs with id's starting with {name}-checkbox
      // and add a click event to them
      // Use normal javasript dom events so they can be triggered with event propagation
      this.el[0]
        .querySelectorAll(`[id*=advanced-search-dropdown-${this.options.name}]`)
        .forEach((value, index, arr) => {
          value.onchange = (e) => {
            this._onToggleItem(e);
            changes = true;
          }
        });
    },

    _onToggleMultiSelect: function(el) {
      el.toggleClass("expanded");
    },

    _onToggleItem: function(e) {
      const value = e.target.dataset.optionValue;

      // Add custom item functionality if allowAll is active
      // Such as checking all checkboxes when the 'all' checkbox is selected
      if (this.options.allowAll) {
        // Handle clicking the all button
        if (value === "all") {
          const elements = this.checkboxes();
          if (e.target.checked) {
            this.setAllCheckboxes(true, elements);
          } else {
            this.setAllCheckboxes(false, elements);
          }
        }

        if (this.isAllSelected()) {
          this.checkboxes("all")[0].checked = true;
        } else {
          this.checkboxes("all")[0].checked = false;
        }
      }

      this.setStatusText(this.el, this._makeStatusText());
    },

    // Sets the checked value to all elements at the same time
    setAllCheckboxes: function(value, elements) {
      for (let element of elements) {
        element.checked = value;
      }
    },

    setStatusText: function(elem, text) {
      elem.find(".multiselect-status").html(text);
    },

    _makeStatusText: function() {
      const checkboxes = this.checkboxes();
      const selectedItems = [];
      for (let checkbox of checkboxes) {
        if (checkbox.checked) selectedItems.push(checkbox);
      }

      if (this.isAllSelected()) {
        return this.options.allTranslation;
      }

      if (selectedItems.length === 1) {
        return selectedItems[0].dataset.optionLabel;
      }

      return `${selectedItems.length} ${this.options.selectTranslation}`;
    },

    // Returns array of checkboxes with specific name value combo
    checkboxes: function(value = "") {
      return this.el.find(`input[id*=${this.options.name}-checkbox-${value}]`);
    },

    // Returns true if all checkboxes are selected
    // Doesn't include the 'all' checkbox
    isAllSelected: function() {
      const checkboxes = this.checkboxes();
      let checked = true;
      for (let checkbox of checkboxes) {
        if (!checkbox.checked && checkbox.dataset.optionValue !== "all") {
          checked = false;
        }
      }
      return checked;
    }
  };
});
