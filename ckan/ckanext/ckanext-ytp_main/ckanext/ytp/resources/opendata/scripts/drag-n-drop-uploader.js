this.ckan.module('drag-n-drop-uploader', function($) {
    return {
      /* options object can be extended using data-module-* attributes */
      options: {},
  
      initialize: function () {
        var dropzones = document.querySelectorAll('.dropzone');
        if (dropzones.length > 0) {
          dropzones.forEach(this.initializeDropzone);
        }
      },
  
      initializeDropzone(dropzone) {
        var input = dropzone.querySelector('[type="file"]');
  
        dropzone.ondragover = function (e) { 
          e.preventDefault(); 
          this.classList.add('dropzone--hover');
        };
        dropzone.ondragleave = function (e) { 
            e.preventDefault();
            this.classList.remove('dropzone--hover');
        };
        dropzone.ondrop = function (e) {
            e.preventDefault();
            this.classList.remove('dropzone--hover');
            input.files = e.dataTransfer.files;
            $(input).trigger('change');
        }
      }
    }
})
  