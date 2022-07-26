var LocationSearch = function() {
  var self = {
    locationApiUrl: '',
    locationInput: '',
  }

  function init() {
    self.locationApiUrl = $('#location-meta-data').data().locationApiUrl;
    self.locationInput = $('#field-location');

    loadDataAndInitSelec2();
    attachSelectOnchangeEvent();
  }

  function formatLocationSelection(data) {
    return '<option value="'+ data.id +'">' + data.text + '</option>';
  }

  function loadDataAndInitSelec2() {
    $.ajax({
      url: self.locationApiUrl,
      type: 'GET',
      dataType: 'json',
      success: function(res) {
        initSelect2(res.results);
      }
    });
  }

  function initSelect2(data) {
    self.locationInput.select2({
      data: data,
      minimumInputLength: 2,
      formatSelection: formatLocationSelection,
      escapeMarkup: function (m) { return m; },
    });
  }

  function attachSelectOnchangeEvent() {
    self.locationInput.change(function(e) {
      // Format of coordinates: [0] = lng_min, [1] = lat_ min, [2] = lng_max, [3] = lat_max
      var coords = e.val.split(',');

      // Get points in order for drawing a box according to the Leaflet specs
      var coordsStr = coords[0] + ',' + coords[1] + ',' + coords[2] + ',' + coords[3];

      // Set hidden input values for the search
      $('#ext_bbox').val(coordsStr);
      $('#ext_prev_extent').val(coordsStr);

      // Get and post form
      var form = $("#dataset-search");
      if (!form.length) { form = $(".search-form"); }

      setTimeout(function() {
        form.submit();
      }, 800);
    });
  }

  return {init: init};
}();

$(document).ready(function() {
  LocationSearch.init();
});