// Quides page search with and without login to service
describe('Guides search functionality', function() {
  // TODO: Haku tehdään sekä kirjautuneena että ilman sitä
  // TODO: Haun Teko

  // Without login
  //it('Guides search basic', function() {
  it('Visitor opens guide front page', function () {
    cy.visit("/");
    cy.visit("/fi/opas");
  })

  it('Visitor uses guide search', function () {
    cy.get('#guide-search-field').click();
    cy.get('#guide-search-field').type('helsinki');
    cy.get('#guide-search-button').click();
    //cy.visit('http://vagrant.avoindata.fi:9000/data/fi/dataset?q=helsinki')
  })


  // With login
  it('Logged in user opens guide front page', function () {
    cy.login_post_request('test-publisher', 'test-publisher');
    cy.visit("/");
    cy.visit("/fi/opas");
  })

  it('Logged in user uses guide search', function () {
    const options = {scrollBehavior: 'center'};
    cy.get('#guide-search-field').click();
    cy.get('#guide-search-field').type('helsinki');
    cy.get('#guide-search-button').click();
    //cy.visit('http://vagrant.avoindata.fi:9000/data/fi/dataset?q=helsinki')
  })

})
