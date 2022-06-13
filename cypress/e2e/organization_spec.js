describe("Organization tests", function() {

  beforeEach(function(){
    cy.reset_db();
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/');
    cy.get('nav a[href="/data/fi/organization"]').click();
  });

  it('Create, edit and delete organization', function(){
    cy.get('a[href="/data/fi/organization/new"]').click();

    // Create organization
    const organization_name = 'create_edit_delete_test_organization';
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get("input[name='name']").type(organization_name);
    cy.get("input[name='title_translated-fi']").type(organization_name);
    cy.get('button[name="save"]').click();
    cy.url().should('include', `/data/fi/organization/${organization_name}`);
    cy.get(`.nav.nav-tabs a[href="/data/fi/organization/${organization_name}"]`).parent().should('have.class', 'active');

    // Edit
    cy.get(`a[href='/data/fi/organization/edit/${organization_name}']`).click();
    cy.get(`input[id='field-title_translated-fi'][value='${organization_name}'`).type('edit');
    cy.get('button[name=save]').click();
    cy.get('.heading').contains(organization_name+'edit');
     
    //Delete
    cy.get(`a[href='/data/fi/organization/edit/${organization_name}']`).click(); // Url shouldn't have changed
    cy.get('.form-actions').contains('Poista').click();
    cy.get('body').then($body =>{
      if ($body.find('.modal-dialog').length > 0 ){
        cy.get('.modal-dialog').find('.btn').contains('Vahvista').click()
      }
      else {
        // Delete UI was rendered on its own page
        cy.get('body').find('.btn').contains('Vahvista').click();
      }
    })


    cy.get('input[data-organization-filter]').type(organization_name);
    cy.get('.search-form button[type="submit"]').first().click();
    cy.get('.organization-list').find('li').should('have.length', 0);
  })

  it('Organization data should be in the UI', function() {
    cy.get('a[href="/data/fi/organization/new"]').click();

    // Create organization
    const organization_name = 'organization_data_test';
    const organization_notes = 'organization_notes';
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get("input[name='name']").type(organization_name);
    cy.get("input[name='title_translated-fi']").type(organization_name);
    cy.get("input[name='title_translated-sv']").type(organization_name + '_sv');
    cy.get("input[name='title_translated-en']").type(organization_name + '_en');
    cy.get("textarea[name='description_translated-fi']").type(organization_notes);
    cy.get("textarea[name='description_translated-sv']").type(organization_notes + '_sv');
    cy.get("textarea[name='description_translated-en']").type(organization_notes + '_en');
    cy.get('button[name="save"]').click();

    cy.get('.heading').should('have.text', organization_name);

    cy.switch_language('sv');
    cy.get('.heading').should('have.text', organization_name + '_sv');

    cy.switch_language('en');
    cy.get('.heading').should('have.text', organization_name + '_en');

    cy.switch_language('fi');

    cy.get(`a[href="/data/fi/organization/about/${organization_name}"]`).click();
    cy.get('.about-organization .notes').should('contain.text', organization_notes);

    cy.switch_language('sv');
    cy.get('.about-organization .notes').should('contain.text', organization_notes + '_sv');

    cy.switch_language('en');
    cy.get('.about-organization .notes').should('contain.text', organization_notes + '_en');
  })

  it('Creating an empty organization fails', function() {
    cy.get('a[href="/data/fi/organization/new"]').click();
    cy.get('button[name=save]').click();
    cy.get('.error-explanation');

  })

  it('Cannot create organization if logged out', function() {
    cy.logout();
    cy.visit('/');
    cy.get('nav a[href="/data/fi/organization"]').click();
    cy.get('a[href="/data/fi/organization/new"]').should('not.exist');
  })
});
