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
    const organization_name = 'test_organization';
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get("input[name='name']").type(organization_name);
    cy.get("input[name='title_translated-fi']").type(organization_name);
    cy.get('button[name="save"]').click();
    cy.url().should('include', `/data/fi/organization/${organization_name}`);

    // Edit
    cy.get(`a[href='/data/fi/organization/edit/${organization_name}']`).click();
    cy.get(`input[id='field-title_translated-fi'][value='${organization_name}'`).type('edit');
    cy.get('button[name=save]').click();
    cy.get('.heading').contains(organization_name+'edit');
     
    //Delete
    cy.get(`a[href='/data/fi/organization/edit/${organization_name}']`).click(); // Url shouldn't have changed
    cy.get('.form-actions').contains('Poista').click();
    cy.get('.modal-dialog').find('.btn').contains('Vahvista').click();
    cy.get('input[data-organization-filter]').type(organization_name);
    cy.get('.organization-tree').find('.organization-list-item:visible').should('have.length', 0);
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
