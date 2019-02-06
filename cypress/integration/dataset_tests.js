describe('Dataset tests', function() {

    beforeEach(function () {
      cy.login_post_request('test-user', 'test-user')
      cy.visit('/');
      cy.get('nav a[href="/data/fi/dataset"]').click();
    })

    it('Create a new minimal dataset, edit it and delete it', function() {
      // Dataset form
      cy.get('a[href="/data/fi/dataset/new"]').click();

      const dataset_name = 'test_dataset';
      cy.get("input[id='field-title_translated-fi']").type(dataset_name);
  
      cy.get('.slug-preview button').contains('Muokkaa').click();
      cy.get('#field-name').type(dataset_name);
      cy.get('#field-notes_translated-fi').type('Dataset test description');
      cy.get('#s2id_autogen1').type('test_keyword {enter}');
      cy.get('#field-maintainer').type('test maintainer');
      cy.get('#field-maintainer_email').type('test.maintainer@example.com');
      cy.get('button[name=save]').click();

      // Resource form
      cy.get('input[id=field-name_translated-fi]').type('test data');
      cy.get('.form-actions button').contains('Valmis').click();
      cy.url().should('include', `/data/fi/dataset/${dataset_name}`);

      // Edit
      cy.get(`a[href='/data/fi/dataset/edit/${dataset_name}']`).click();
      cy.get(`input[id='field-title_translated-fi'][value='${dataset_name}'`).type('edit');
      cy.get('button[name=save]').click();
      cy.get('.dataset-title-column').contains(dataset_name+'edit');
       
      //Delete
      cy.get(`a[href='/data/fi/dataset/edit/${dataset_name}']`).click(); // Url shouldn't have changed
      cy.get('.form-actions').contains('Poista').click();
      cy.get('#page_wrapper').find('.btn').contains('Vahvista').click();
      cy.get('.search-input .search').type(dataset_name + '{enter}');
      cy.get('.dataset-list').should('not.exist');
      cy.contains("ei löytynyt tietoaineistoja");
    })
  
    it('Creating an empty dataset fails', function() {
      cy.get('a[href="/data/fi/dataset/new"]').click();
      cy.get('button[name=save]').click();
      cy.get('.error-explanation');

    })

    it('Cannot create dataset if logged out', function() {
      cy.logout();
      cy.visit('/');
      cy.get('nav a[href="/data/fi/dataset"]').click();
      cy.get('a[href="/data/fi/dataset/new"]').should('not.exist');
    })
})
