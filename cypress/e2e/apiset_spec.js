describe('Apiset tests', function() {

  beforeEach(function () {
    cy.reset_db();
    cy.create_organization_for_user('apiset_test_organization', 'test-user', true);
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/');
    // Apiset is not currently included in nav
    // cy.get('nav a[href="/data/fi/apiset"]').click();
  });

  it('Create a new minimal api, edit it and delete it', function() {
    const apis_name = 'test_api';
    cy.create_new_apiset(apis_name);
    cy.edit_apiset(apis_name);

    // Delete and make sure it was deleted. Edit doesn't affect the apiset name in url, so the unmodified
    // name is passed as a parameter
    cy.delete_apiset(apis_name);
  });

  it("Create minimal apiset and add file as a api", function(){
    const apiset = 'test_apiset_with_file';

    const apiset_form_data = {
      "#field-title_translated-fi": apiset,
      '#field-notes_translated-fi': 'Apiset test description',
      // FIXME: This should just be 'test_keyword{enter}', see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
      '#field-api_provider': 'Api Provider',
      '#field-api_provider_email': 'test.provider@example.com'
    };

    cy.visit('/data/fi/apiset/new');
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get('#field-name').type(apiset);
    cy.fill_form_fields(apiset_form_data);
    cy.get('button[name=save]').click();


    const api = 'sample file';
    const api_form_data = {
      "#field-name_translated-fi": api
    };
    cy.fill_form_fields(api_form_data);

    cy.get('#field-image-upload').selectFile("cypress/FL_insurance_sample.csv")

    cy.get('button[name=save].suomifi-button-primary').click();

    // if cloudstorage is enabled, we wait for window.location to change
    if (Cypress.env('cloudStorageEnabled')){
      cy.location('pathname', {timeout: 20000}).should('not.include', '/resource/new');
    }

    cy.get('a').contains(api).click();

    cy.get('a').contains('Lataa')
      .should('have.attr', 'href')
      .then(function (href) {
        cy.request(href).its('status')
          .should('eq', 200)
    });
  });

  it('Create an apiset with all fields', function() {
    const apiset_name = 'test_apiset_with_all_fields';
    const apiset_form_data = {
      '#field-title_translated-fi': apiset_name,
      '#field-title_translated-en': apiset_name,
      '#field-title_translated-sv': apiset_name,
      '#field-notes_translated-fi': 'test kuvaus',
      '#field-notes_translated-en': 'test description',
      '#field-notes_translated-sv': 'test beskrivning',
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test']},
      '#s2id_autogen2': {type: 'select2', values: ['test']},
      '#s2id_autogen3': {type: 'select2', values: ['test']},
      '#field-private': 'False',
      '#field-license_id': 'cc-by-4.0',
      '#field-terms_of_service-fi': 'Ehdot',
      '#field-terms_of_service-en': 'Ehdot',
      '#field-terms_of_service-sv': 'Ehdot',
      '#field-access_rights-fi': 'Käyttöoikeudet',
      '#field-access_rights-en': 'Käyttöoikeudet',
      '#field-access_rights-sv': 'Käyttöoikeudet',
      '#field-api_provider': 'Api Provider',
      '#field-api_provider_email': 'test.provider@example.com',
    };

    const api_form_data = {
      '#field-name_translated-fi': 'test api',
      '#field-name_translated-en': 'test api',
      '#field-name_translated-sv': 'test api',
      '#field-image-url': 'http://example.com',
      '#field-description_translated-fi': 'test kuvaus',
      '#field-description_translated-en': 'test description',
      '#field-description_translated-sv': 'test beskrivning',
      '#field-documentation_translated-fi': 'test dokumentaatio',
      '#field-documentation_translated-en': 'test dokumentaatio',
      '#field-documentation_translated-sv': 'test dokumentaatio',
      '[name="registration_required"]': {type: 'radio', value: 'true', force: true},
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['Päivittäin']},
      '#s2id_autogen2': {type: 'select2', values: ['Päivittäin']},
      '#s2id_autogen3': {type: 'select2', values: ['Päivittäin']}
    };
    cy.create_new_apiset(apiset_name, apiset_form_data, api_form_data);
  });

  it('Creating an empty apiset fails', function() {
    cy.visit('/data/fi/apiset/new');
    cy.get('button[name=save]').click();
    cy.get('.error-explanation');
  });

  it('Cannot create apiset if logged out', function() {
    cy.logout_request();
    cy.visit(('/data/fi/apiset/new'), {
      failOnStatusCode: false
    });
    cy.contains('Ei oikeuksia luoda tietoaineistoa');
  });
})
