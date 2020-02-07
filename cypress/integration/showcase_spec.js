describe('Showcase tests', function() {

  beforeEach(function () {
    cy.reset_db();
  });

  it('Create a new minimal showcase, edit it and delete it', function() {
    cy.add_showcase_user();
    const showcase_name = 'test_showcase';
    cy.create_new_showcase(showcase_name);
    cy.edit_showcase(showcase_name);

    // Delete and make sure it was deleted. Edit doesn't affect the showcase name in url, so the unmodified
    // name is passed as a parameter
    cy.delete_showcase(showcase_name);
  });

  it('Create a showcase with all fields', function() {
    cy.add_showcase_user();
    const showcase_name = 'test_showcase_with_all_fields';
    const showcase_form_data = {
      '#field-title': showcase_name,
      '#s2id_autogen1': 'test {enter}',
      '#s2id_autogen2': 'test {enter}',
      '#s2id_autogen3': 'test {enter}',
      '#s2id_autogen4': 'test {enter}',
      '#s2id_autogen6': 'test {enter}',
      '#s2id_autogen7': 'test {enter}',
      '#field-author': 'test {enter}',
      '#field-author_website': 'www.example.com',
      '#field-application_website': 'www.example.com',
      '#field-store_urls': 'www.example.com',
      '#field-notes_translated-fi': 'test kuvaus',
      '#field-notes_translated-en': 'test description',
      '#field-notes_translated-sv': 'test beskrivning'
    };

    cy.create_new_showcase(showcase_name, showcase_form_data);
  });

  it('Cannot create showcase if logged out', function() {
    cy.visit('/');
    cy.get('nav a[href="/data/fi/showcase"]').click();
    cy.get('a[href="/data/fi/showcase/new"]').should('not.exist');
  })

  it('Fill showcase form with anonymous user', function() {
    cy.visit('/');
    cy.get('nav a[href="/data/fi/showcase"]').click();
    cy.create_new_showcase_using_public_form("testisovellus");
    cy.get("testisovellus").should('not.exist'); // The showcase should not be visible on the list
  })

  it('Add dataset to showcase and edit showcase with dataset', function() {

    cy.add_showcase_user();
    cy.logout_request();

    // Organization
    cy.login_post_request('admin', 'administrator');
    const organization_name = 'testi_organisaatio';
    cy.create_new_organization(organization_name);
    cy.approve_organization(organization_name);
    cy.visit(`/data/fi/organization/member_new/${organization_name}`);
    cy.get('#s2id_username').click();
    cy.get('#s2id_autogen1_search').type('test-publisher{enter}', {force: true});
    cy.get('#s2id_role').click();
    cy.get('#s2id_autogen2_search').type('admin{enter}', {force: true});
    cy.get('button[type=submit]').click();
    cy.logout_request();


    cy.login_post_request('test-publisher', 'test-publisher');

    cy.visit(`/data/fi/organization/${organization_name}`)

    // Dataset linked to organization
    const dataset_form_data = {
      "#field-title_translated-fi": 'test dataset',
      '#field-notes_translated-fi': 'Dataset test description',
      '#s2id_autogen1': 'test_keyword {enter}',
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': 'test.maintainer@example.com',
    }
    cy.get('nav a[href="/data/fi/dataset"]').click();
    // Dataset will be created with default resource_form_data
    const resource_form_data = null;
    const showcase_name = "test-showcase";
    cy.create_new_dataset("test dataset", dataset_form_data, resource_form_data, organization_name);

    // Create a showcase with dataset
    cy.create_new_showcase(showcase_name);
    //cy.get(`a[href="/data/fi/showcase/edit/${showcase_name}"]`).click();
    //cy.get(`a[href="/data/fi/showcase/manage_datasets/${showcase_name}"]`).click();
    cy.visit(`/data/fi/showcase/manage_datasets/${showcase_name}`)
    //There should be only one checkbox, because there is only one dataset
    cy.get("tbody td input").first().click();
    cy.get('button[name="bulk_action.showcase_add"]').click()
    //Remove button should exist after adding the dataset
    cy.get('button[name="bulk_action.showcase_remove"')
    cy.get(`a[href="/data/fi/showcase/${showcase_name}"]`).first().click();
    cy.edit_showcase(showcase_name);
  })

  it('Creating an empty showcase fails', function() {
    cy.add_showcase_user();
    cy.get('a[href="/data/fi/showcase/new"]').click();
    cy.get('button[name=save]').click();
    cy.get('.error-explanation');
  });
  
});
