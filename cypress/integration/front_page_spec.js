describe('Basic tests', function() {
  before(function () {
    // Ensure platform vocabulary for submit-showcase
    cy.reset_db();
  });


  it('Opens frontpage!', function() {
    cy.visit("/");
  });

  // Opens pages, which don't require a certain dataset, resource, organization
  // or other item to exist. Only tests that the url doesn't return an error code
  it('Opens all kinds of various pages', function() {
    cy.request("/data/dataset");
    cy.request("/data/sv/dataset");
    cy.request("/data/en_GB/dataset");
    cy.request("/data/dataset?tags=test");
    cy.request("/data/organization");
    cy.request("/data/fi/organization");
    cy.request("/data/sv/organization");
    cy.request("/data/en_GB/organization");
    cy.request("/data/showcase");
    cy.request("/data/fi/showcase");
    cy.request("/data/sv/showcase");
    cy.request("/data/en_GB/showcase");
    cy.request("/data/submit-showcase");
    cy.request("/data/group");
    cy.request("/data/api/3");
    cy.request("/artikkelit");
    cy.request("/en/articles");
    cy.request("/sv/artiklar");
    cy.request("/fi/artikkelit");
    cy.request("/kayttoohjeet");
    cy.request("/fi/kayttoohjeet");
    cy.request("/en/user-guide");
    cy.request("/sv/bruksanvisningar");
    cy.request("/user/register");
    cy.request("/contact");
    cy.request("/tapahtumat");
    cy.request("/fi/tapahtumat");
    cy.request("/en/events");
    cy.request("/sv/evenemanger");
  })
});

describe('Login page', function(){
  it('Logs in', function(){
    cy.login('admin', 'administrator');
  });
  it('Logs out', function(){
    cy.login_post_request('admin', 'administrator');
    cy.logout();
  })
});

describe('Test contact page', function () {
  it('Sending feedback should succeed', function () {
    cy.visit('/contact');
    cy.get('#edit-name').type("Some name");
    cy.get('#edit-mail').type('foo@example.com');
    cy.get('#edit-subject-0-value').type('Some subject');
    cy.get('#edit-message-0-value').type('Some content for feedback');
    cy.get('#edit-submit').click();
    cy.get('.messages__wrapper').contains('Your message has been sent.')
  });

  it('Sending feedback containing site url should succeed', function () {
    cy.visit('/contact');
    cy.get('#edit-name').type("Some name");
    cy.get('#edit-mail').type('foo@example.com');
    cy.get('#edit-subject-0-value').type('Some subject');
    cy.get('#edit-message-0-value').type('This content contains url to site https://www.avoindata.fi');
    cy.get('#edit-submit').click();
    cy.get('.messages__wrapper').contains('Your message has been sent.')
  });

  it('Sending feedback containing external url should fail', function () {
    cy.visit('/en/contact');
    cy.get('#edit-name').type("Some name");
    cy.get('#edit-mail').type('foo@example.com');
    cy.get('#edit-subject-0-value').type('Some subject');
    cy.get('#edit-message-0-value').type('This content contains url to external site http://example.com');
    cy.get('#edit-submit').click();
    cy.get('.messages__wrapper').children('div').should('have.class', 'alert-danger').contains('spam content')
  });

});
