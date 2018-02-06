jQuery(document).ready(function($) {

  var initializePhotoswipe = function(images, clickedImageIndex) {
    if(images.length > 0) {
      var gallery = new PhotoSwipe(
          document.querySelectorAll('.pswp')[0],
          PhotoSwipeUI_Default,
          images,
          { index: clickedImageIndex, x: 0, y: 0 }
      );

      gallery.init();
    }
  };

  $(".image-modal-open").click(function () {
    var clickedImageElement = $(this)[0];
    var clickedImageIndex = 0;

    var imageElements = $('.image-slider').find('img');
    var images = [];

    for(var i = 0; i < imageElements.length; i++) {
      if(imageElements[i].src === clickedImageElement.src) {
        clickedImageIndex = i;
      }
      images.push({
        src: imageElements[i].src,
        w: imageElements[i].width*3, // Image can be safely scaled 3x since photoswipe will autoscale it to fit the screen
        h: imageElements[i].height*3,
        pid: imageElements[i].alt
      })
    }

    initializePhotoswipe(images, clickedImageIndex);
  });
});