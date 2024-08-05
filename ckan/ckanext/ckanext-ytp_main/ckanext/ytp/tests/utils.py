def minimal_dataset_with_one_resource_fields(user):
    return dict(
        user=user,
        private=False,
        title_translated={'fi': 'Title (fi)'},
        notes_translated={'fi': 'Notes (fi)'},
        maintainer='maintainer',
        keywords={'fi': ['test-fi']},
        license_id="licence_id",
        collection_type="Open Data",
        resources=[dict(
            url='http://example.com'
        )]
    )


