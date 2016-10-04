$(document).ready(function(){
    $('[data-organization-tree] .js-expand').bind('click', function(){
        $(this).siblings('.js-collapse, .js-collapsed').show();
        $(this).hide();
    });

    $('[data-organization-tree] .js-collapse').bind('click', function(){
        $(this).hide().siblings('.js-collapsed').hide();
        $(this).siblings('.js-expand').show();
    });

    $('[data-organization-filter]').bind('keyup cut paste', function(){
        var search_str = $(this).val().toLowerCase();

        if (search_str.length != 0){
            $('.js-collapse, .js-expand').hide();
            $('.js-collapsed').show();
            var organizations = $('.organization-row');
            organizations.hide();
            var count = 0;
            organizations.filter(function(index, element){
                return element.textContent.toLowerCase().indexOf(search_str) >= 0
            }).each(function(index, element){
                var text = $(element).find('a').get(0).textContent;
                var str_index = text.toLowerCase().indexOf(search_str);
                if ( str_index >= 0){
                    count++;
                    $(this).find('a').html(text.substr(0, str_index) + '<span class="highlight">' + text.substr(str_index, search_str.length) + '</span>' + text.substr(str_index + search_str.length))[0];
                }
            }).show();
        }
        else{
            count = $('.organization-row').length;
            $('span.highlight').contents().unwrap()
            $('.organization-row').show();
            $('.js-collapsed').hide();
            $('.js-expand').show();
        }

        var count_str = $('.search-form h1').text();
        var replaced = count_str.replace(/\d+/g, count);
        $('.search-form h1').text(replaced);
    })
});