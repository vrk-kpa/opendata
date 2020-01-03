// Quides page search with and without login to service
describe('Guides search functionality', function() {
    // TODO: Haku tehdään sekä kirjautuneena että ilman sitä
    // TODO: Haun Teko
  
    // Without login
    //it('Guides search basic', function() {
    it('Opens frontpage!', function () {
      cy.visit("/");
      cy.visit("/fi/artikkelit");
    })

    it('Hae', function () {
      cy.get('#avoindata-articles-search-input').click();
      cy.get('#avoindata-articles-search-input').type('helsinki');
      cy.get('#avoindata-articles-search-btn').click();
      //cy.visit('http://vagrant.avoindata.fi:9000/data/fi/dataset?q=helsinki')
      })
    })

 // With login
    it('Opens frontpage!', function () {
        cy.login_post_request('test-publisher', 'test-publisher');
        cy.visit("/");
        cy.visit("/fi/artikkelit");
    })

    it('Hae', function () {
        cy.get('#avoindata-articles-search-input').click();
        cy.get('#avoindata-articles-search-input').type('helsinki');
        cy.get('#avoindata-articles-search-btn').click();
        //cy.visit('http://vagrant.avoindata.fi:9000/data/fi/dataset?q=helsinki')
    })
  
