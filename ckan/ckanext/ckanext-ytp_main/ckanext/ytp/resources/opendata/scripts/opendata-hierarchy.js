$(document).ready(function(){
  $('[data-organization-tree] .js-expand').bind('click', function(){
    // Separate rule for buttons since .show() results in 'block'
    $(this).siblings('.js-collapse.btn').css('display', 'inline');

    $(this).siblings('.js-collapse, .js-collapsed').show()
    $(this).hide();
  });

  $('[data-organization-tree] .js-collapse').bind('click', function(){
    $(this).hide().siblings('.js-collapsed').hide();
    $(this).siblings('.js-expand').show()
  });
});
