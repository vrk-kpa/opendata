describe('Dataset tests', function() {

  beforeEach(function () {
    cy.reset_db();
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/');
    cy.get('nav a[href="/data/fi/dataset"]').click();
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
      '#s2id_autogen1': 'test_keyword {enter}',
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

    cy.get('#field-image-upload').then(function(subject){
      cy.fixture("FL_insurance_sample.csv", 'base64')
        .then(Cypress.Blob.base64StringToBlob)
        .then(function(blob){
          const el = subject[0];
          const testFile = new File([blob],"FL_insurance_sample.csv", {type: 'CSV'} );
          const dataTranfer = new DataTransfer();
          dataTranfer.items.add(testFile);
          el.files = dataTranfer.files;
        })
    });

    cy.get('button[name=save]').contains('Valmis').click();

    cy.get('a').contains(resource_name).click();

    cy.get('a').contains('Avaa')
      .should('have.attr', 'href')
      .then(function (href) {
        cy.request(href).its('status')
          .should('eq', 200)
    })
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
      '#s2id_autogen1': 'test {enter}',
      '#s2id_autogen2': 'test {enter}',
      '#s2id_autogen3': 'test {enter}',
      '#s2id_autogen4': 'test {enter}',
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': 'example@example.com',
      '#field-maintainer_website': 'www.example.com',
      '#field-owner': 'Test',
      '#field-copyright_notice_translated-fi': 'lisenssi test',
      '#field-copyright_notice_translated-en': 'lisenssi test',
      '#field-copyright_notice_translated-sv': 'lisenssi test',
      '#s2id_autogen6': 'test',
      '#s2id_autogen7': 'test',
      '#s2id_autogen8': 'test',
      '#field-external_urls': 'www.example.com',
      '#field-author': 'test',
      '#field-author_email': 'test@example.com',
      '#field-valid_from': '2019-02-04',
      '#field-valid_till': '2020-02-04'
    };

    const resource_form_data = {
      '#field-name_translated-fi': 'test data',
      '#field-name_translated-en': 'test data',
      '#field-name_translated-sv': 'test data',
      '#field-description_translated-fi': 'test kuvaus',
      '#field-description_translated-en': 'test description',
      '#field-description_translated-sv': 'test beskrivning',
      '#field-position_info': '56.7 43.5',
      '#field-time_series_start': '2019-02-04',
      '#field-time_series_end': '2020-02-04',
      '#s2id_autogen2': '2 viikkoa',
      '#s2id_autogen3': '2 viikkoa',
      '#s2id_autogen4': '2 viikkoa',
      '#field-temporal_granularity-fi': 'test',
      '#field-temporal_granularity-en': 'test',
      '#field-temporal_granularity-sv': 'test',
      '#field-update_frequency-fi': 'test',
      '#field-update_frequency-en': 'test',
      '#field-update_frequency-sv': 'test',
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
    cy.logout();
    cy.visit('/');
    cy.get('nav a[href="/data/fi/dataset"]').click();
    cy.get('a[href="/data/fi/dataset/new"]').should('not.exist');
  })
})
