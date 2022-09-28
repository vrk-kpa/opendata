describe('Articles page', function() {

  it("Navigate to article page", function(){
    cy.visit("/");
    cy.get('.nav > :nth-child(5) > a').click();
    cy.location('pathname', {timeout: 60000}).should('contain', `/artikkelit`);
  });

  // This is an old test that should be expanded upon at some point
  it("Search for an article", function(){
    cy.visit("/fi/artikkelit");
    const options = {scrollBehavior: 'center'};
    cy.get('#avoindata-articles-search-input').click(options);
    cy.get('#avoindata-articles-search-input').type('helsinki');
    cy.get('#avoindata-articles-search-btn').click(options);
  });

  it('User creates an article', function() {
    cy.visit('/')
    cy.login_post_request('test-publisher', 'test-publisher');
    cy.visit('/fi/node/add')
    cy.contains('Avoindata Article').click();

    const news_name = 'news_test';
    const news_form_data = {
     "#edit-title-0-value": 'news_name',                                      
     '#id=editlangcode-0-value': 'Kielivalinta',                              
     '#cke_wysiwyg_frame cke_reset': 'tähän tulee juttua {enter}',            
     '#field-maintainer': '',                                                    
     '#edit-field-tags-target-id': 'Helsinki, Turku, Tampere, Hämeenlinna'
    };

    // Title field
    cy.get('#edit-title-0-value').click({force:true}).type(news_name)
    cy.get('#edit-langcode-0-value').select('fi', {force: true})
    cy.get('#edit-field-tags-target-id').click({force: true}).type('test')

    // Save
    cy.contains('Tallenna').click()
  })

})
