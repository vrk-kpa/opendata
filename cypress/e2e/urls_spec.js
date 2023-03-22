describe('URL tests', function(){

    // Perform get requests to various urls in order to test if they return an error code
    // NOTE! Might be unnecessary, but keeping it for now
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
      cy.request("/sv/evenemang");
    })
  })