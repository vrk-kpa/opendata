(function ($) {
  $(document).ready(function () {
    // Google Analytics event tracking

    // group links on home page
    $('body.home div.group a').click(function() {
      _gaq.push(['_trackEvent', 'Home', 'Click: Group Link', $(this).attr('href')]);
    });

    // clicking on user name (go to profile)
    $('div.account span.ckan-logged-in a').first().click(function() {
      _gaq.push(['_trackEvent', 'User', 'Click: User Name', $(this).attr('href')]);
    });

    // In user profile, clicking on Edit Profile
    $('body.user div#minornavigation a')
      .filter(function(index) {return $(this).text() === "Edit Profile";})
      .click(function() {
      _gaq.push(['_trackEvent', 'User', 'Click: Tab', 'Edit Profile']);
    });

    // Clicking Save Changes on Edit Profile page
    $('body.user.edit input#save').click(function() {
      _gaq.push(['_trackEvent', 'User', 'Click: Button', 'Save Profile Changes']);
    });

    // Clicking on any dataset link on User Profile page
    $('body.user.read ul.datasets a').click(function() {
      _gaq.push(['_trackEvent', 'User', 'Click: Dataset Link', $(this).attr('href')]);
    });

    // Compare Button on /dataset/history/X
    $('body.package.history form#dataset-revisions input[name="diff"]').click(function() {
      _gaq.push(['_trackEvent', 'Dataset', 'Click: Button', 'Compare History']);
    });

    // Tags on right hand sidebar of /dataset/X
    $('body.package.read div#sidebar h3')
      .filter(function(index) {return $(this).text().indexOf("Tags") != -1;})
      .next('ul')
      .find('a')
      .click(function() {
      _gaq.push(['_trackEvent', 'Dataset', 'Click: Tag', $(this).attr('href')]);
    });

    // Any of the group links on /group
    $('body.group.index table.groups a').click(function() {
      _gaq.push(['_trackEvent', 'Group', 'Click: Group Link', $(this).attr('href')]);
    });

    // Clicking any of the right hand sidebar tags on /group/X
    $('body.group.read div#sidebar h2')
      .filter(function(index) {return $(this).text().indexOf("Tags") != -1;})
      .next('ul')
      .find('a')
      .click(function() {
      _gaq.push(['_trackEvent', 'Group', 'Click: Tag', $(this).attr('href')]);
    });

    // Visiting /group/history/X
    $('body.group div#minornavigation ul.nav a')
      .filter(function(index) {return $(this).text().indexOf("History") != -1;})
      .click(function() {
      _gaq.push(['_trackEvent', 'Group', 'Click: History Tab', $(this).attr('href')]);
    });

    // Compare Button on /group/history/X
    $('body.group.history form#group-revisions input[name="diff"]').click(function() {
      _gaq.push(['_trackEvent', 'Group', 'Click: Button', 'Compare History']);
    });
  });
}(jQuery));
