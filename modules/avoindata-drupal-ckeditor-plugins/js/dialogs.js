// @TODO: Translations should be added some way
CKEDITOR.dialog.add('avoindata_section', function () {
  return {
    title: 'Avoindata section',
    minWidth: 300,
    minHeight: 100,
    contents: [
      {
        id: 'info',
        elements: [
          {
            id: 'id',
            type: 'text',
            label: 'Id',
            setup: function (widget) {
              this.setValue(widget.data.id);
            },
            commit: function (widget) {
              widget.setData('id', this.getValue());
            },
          },
        ],
      },
    ],
  };
});
