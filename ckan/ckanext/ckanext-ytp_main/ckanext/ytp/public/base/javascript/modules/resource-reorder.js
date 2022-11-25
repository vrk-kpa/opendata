/* Module for reordering resources
 */

this.ckan.module('resource-reorder', function($) {
    return {
      options: {
        id: false
      },
      template: {
        title: '<h1></h1>',
        help_text: '<p></p>',
        button: [
          '<a href="javascript:;" class="btn btn-default">',
          '<i class="fa fa-bars"></i>',
          '<span></span>',
          '</a>'
        ].join('\n'),
        form_actions: [
          '<div class="form-actions">',
          '<a href="javascript:;" class="cancel btn btn-danger pull-left"></a>',
          '<a href="javascript:;" class="save btn btn-primary"></a>',
          '</div>'
        ].join('\n'),
        handle: [
          '<a href="javascript:;" class="handle">',
          '<i class="fa fa-arrows"></i>',
          '</a>'
        ].join('\n'),
        saving: [
          '<span class="saving text-muted m-right">',
          '<i class="fa fa-spinner fa-spin"></i>',
          '<span></span>',
          '</span>'
        ].join('\n')
      },
      is_reordering: false,
      cache: false,
  
      initialize: function() {
        jQuery.proxyAll(this, /_on/);
  
        var module = this;
        // Determine texts based on the resource type
        module.sandbox.client.call('POST', 'package_show', {
            id: module.options.id,
          }, function(response) {
            // Get the set type from the response
            let result = response['result'] ?? {};
            let set_type = result['type'] ?? "dataset";

            if (set_type == 'apiset'){
                var labelText = module._('Reorder apiset');
                var helpText = module._('You can rearrange the apiset resources by dragging them using the arrow icon. Drag the resource ' +
                'to the right and place it to the desired location on the list. When you are done, click the "Save order" -button.');
            }
            else{
                var labelText = module._('Reorder resources');
                var helpText = module._('You can rearrange the resources by dragging them using the arrow icon. Drag the resource ' +
                'to the right and place it to the desired location on the list. When you are done, click the "Save order" -button.');
            }

            module.html_title = $(module.template.title)
            .text(labelText)
            .insertBefore(module.el)
            .hide();
    
            module.html_help_text = $(module.template.help_text)
            .text(helpText)
            .insertBefore(module.el)
            .hide();
    
            var button = $(module.template.button)
            .on('click', module._onHandleStartReorder)
            .appendTo('.page_primary_action');
            $('span', button).text(labelText);
    
            module.html_form_actions = $(module.template.form_actions)
            .hide()
            .insertAfter(module.el);
            $('.save', module.html_form_actions)
            .text(module._('Save order'))
            .on('click', module._onHandleSave);
            $('.cancel', module.html_form_actions)
            .text(module._('Cancel'))
            .on('click', module._onHandleCancel);
    
            module.html_handles = $(module.template.handle)
            .hide()
            .appendTo($('.resource-item', module.el));
    
            module.html_saving = $(module.template.saving)
            .hide()
            .insertBefore($('.save', module.html_form_actions));
            $('span', module.html_saving).text(module._('Saving...'));
    
            module.cache = module.el.html();
    
            module.el
            .sortable()
            .sortable('disable');
          });

      },
  
      _onHandleStartReorder: function() {
        if (!this.is_reordering) {
          this.html_form_actions
            .add(this.html_handles)
            .add(this.html_title)
            .add(this.html_help_text)
            .show();
          this.el
            .addClass('reordering')
            .sortable('enable');
          $('.page_primary_action').hide();
          this.is_reordering = true;
        }
      },
  
      _onHandleCancel: function() {
        if (
          this.is_reordering
          && !$('.cancel', this.html_form_actions).hasClass('disabled')
        ) {
          this.reset();
          this.is_reordering = false;
          this.el.html(this.cache)
            .sortable()
            .sortable('disable');
          this.html_handles = $('.handle', this.el);
        }
      },
  
      _onHandleSave: function() {
        if (!$('.save', this.html_form_actions).hasClass('disabled')) {
          var module = this;
          module.html_saving.show();
          $('.save, .cancel', module.html_form_actions).addClass('disabled');
          var order = [];
          $('.resource-item', module.el).each(function() {
            order.push($(this).data('id'));
          });
          module.sandbox.client.call('POST', 'package_resource_reorder', {
            id: module.options.id,
            order: order
          }, function() {
            module.html_saving.hide();
            $('.save, .cancel', module.html_form_actions).removeClass('disabled');
            module.cache = module.el.html();
            module.reset();
            module.is_reordering = false;
          });
        }
      },
  
      reset: function() {
        this.html_form_actions
          .add(this.html_handles)
          .add(this.html_title)
          .add(this.html_help_text)
          .hide();
        this.el
          .removeClass('reordering')
          .sortable('disable');
        $('.page_primary_action').show();
      }
  
    };
  });