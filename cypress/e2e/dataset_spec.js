describe('Dataset tests', function() {

  beforeEach(function () {
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/');
    cy.get('nav a[href="/data/fi/dataset"]').click();
  })

  before(function(){
    cy.reset_db();
    cy.create_organization_for_user('dataset_test_organization', 'test-user', true);
  })

  it('Create a new minimal dataset, edit it and delete it', function() {
    const dataset_name = 'test_dataset';
    cy.create_new_dataset(dataset_name);
    cy.edit_dataset(dataset_name);

    // Delete and make sure it was deleted. Edit doesn't affect the dataset name in url, so the unmodified
    // name is passed as a parameter
    cy.delete_dataset(dataset_name);
  })

  it("Create minimal dataset and add file as a resource", function(){
    const dataset_name = 'test_dataset_with_file';

    const dataset_form_data = {
      "#field-title_translated-fi": dataset_name,
      '#field-notes_translated-fi': 'Dataset test description',
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': 'test.maintainer@example.com'
    };

    cy.get('a[href="/data/fi/dataset/new"]').click();
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get('#field-name').type(dataset_name);
    cy.fill_form_fields(dataset_form_data);
    cy.get('button[name=save]').click();


    const resource_name = 'sample file';
    const resource_form_data = {
      "#field-name_translated-fi": resource_name
    };
    cy.fill_form_fields(resource_form_data);

    cy.get('#field-image-upload').selectFile("cypress/FL_insurance_sample.csv")

    cy.get('button[name=save].suomifi-button-primary').click();

    // if cloudstorage is enabled, we wait for window.location to change
    if (Cypress.env('cloudStorageEnabled')){
      cy.location('pathname', {timeout: 20000}).should('not.include', '/resource/new');
    }

    cy.get('a').contains(resource_name).click();

    cy.get('a').contains('Lataa')
      .should('have.attr', 'href')
      .then(function (href) {
        cy.request(href).its('status')
          .should('eq', 200)
    });

    // File size should be calculated automatically
    // Use 'contain' because of surrounding whitespace
    cy.get('th').contains('Tiedostokoko').next()
      .should('contain.text', '4123652');
  });

  it('Create a dataset with all fields', function() {
    const dataset_name = 'test_dataset_with_all_fields';
    const dataset_form_data = {
      '#field-title_translated-fi': dataset_name,
      '#field-title_translated-en': dataset_name,
      '#field-title_translated-sv': dataset_name,
      '#field-notes_translated-fi': 'test kuvaus',
      '#field-notes_translated-en': 'test description',
      '#field-notes_translated-sv': 'test beskrivning',
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test']},
      '#s2id_autogen2': {type: 'select2', values: ['test']},
      '#s2id_autogen3': {type: 'select2', values: ['test']},
      '#s2id_autogen4': {type: 'select2', values: ['test']},
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': 'example@example.com',
      '#field-maintainer_website': 'www.example.com',
      '#field-copyright_notice_translated-fi': 'lisenssi test',
      '#field-copyright_notice_translated-en': 'lisenssi test',
      '#field-copyright_notice_translated-sv': 'lisenssi test',
      '#field-external_urls': 'http://www.example.com',
      '#field-valid_from': '2019-02-04',
      '#field-valid_till': '2020-02-04'
    };

    const resource_form_data = {
      '#field-name_translated-fi': 'test data',
      '#field-name_translated-en': 'test data',
      '#field-name_translated-sv': 'test data',
      '#field-image-url': 'http://example.com',
      '#field-description_translated-fi': 'test kuvaus',
      '#field-description_translated-en': 'test description',
      '#field-description_translated-sv': 'test beskrivning',
      '#field-position_info': '56.7 43.5',
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      'label[for=field-temporal_granularity-fi] ~ div .select2-choices input': {type: 'select2', values: ['test']},
      'label[for=field-temporal_granularity-en] ~ div .select2-choices input': {type: 'select2', values: ['test']},
      'label[for=field-temporal_granularity-sv] ~ div .select2-choices input': {type: 'select2', values: ['test']},
      '#field-temporal_coverage_to': '2019-02-02',
      '#field-temporal_coverage_from': '2018-02-02'
    };
    cy.create_new_dataset(dataset_name, dataset_form_data, resource_form_data);
  })

  it('Creating an empty dataset fails', function() {
    cy.get('a[href="/data/fi/dataset/new"]').click();
    cy.get('button[name=save]').click();
    cy.get('.error-explanation');

  })

  it('Cannot create dataset if logged out', function() {
    cy.logout_request();
    cy.visit('/');
    cy.get('nav a[href="/data/fi/dataset"]').click();
    cy.get('a[href="/data/fi/dataset/new"]').should('not.exist');
  })
})
