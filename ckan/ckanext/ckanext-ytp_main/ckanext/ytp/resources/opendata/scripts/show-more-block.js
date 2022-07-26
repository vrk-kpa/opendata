'use strict';

ckan.module('show-more-block', function ($) {
    /* A module that allows developer to hide rest of content when max-height is exceeded
    *
    * maxHeight - Maximum height (in pixels) of block before adding show-more-button
    *
    * Examples
    *
    *   <div data-module="show-more-block" data-module-max-height="400">...content...</div>
    *
    */

    return {
        $showMoreButton: null,
        state: 'none',
        options: {
            maxHeight: 465,
        },
        initialize: function () {
            if (parseInt(this.el.height()) > parseInt(this.options.maxHeight)) {
                this.setMaxHeight();
                this.el.addClass('show-less');
                this.state = 'showLess';
                this.addToggleButton();
            }
        },
        setMaxHeight: function() {
            this.el.css({maxHeight: this.options.maxHeight})
        },
        unsetMaxHeight: function() {
            this.el.css({maxHeight: ''})
        },
        addToggleButton: function() {
            this.$showMoreButton = $(`
                <button class="show-more-block__btn btn btn-link">
                    <i class="fal fa-plus"></i>
                    ${this._('Show more')}
                </button>
            `);
            // Fix button positioning after module-container
            const buttonTop = -parseInt(this.el.css('margin-bottom'));
            this.$showMoreButton.css({marginTop: buttonTop})
            this.el.after(this.$showMoreButton);
            this.$showMoreButton.on('click', this.toggleState.bind(this))
        },
        toggleState: function() {
            if (this.state === 'showLess') {
                this.state = 'showMore';
                this.unsetMaxHeight();
                this.el.removeClass('show-less');
                this.$showMoreButton.html(`
                    <i class="fal fa-minus"></i>
                    ${this._('Show less')}
                `)
            } else {
                this.setMaxHeight();
                this.state = 'showLess';
                this.el.addClass('show-less');
                this.$showMoreButton.html(`
                    <i class="fal fa-plus"></i>
                    ${this._('Show more')}
                `)
            }
        }
    }
});
