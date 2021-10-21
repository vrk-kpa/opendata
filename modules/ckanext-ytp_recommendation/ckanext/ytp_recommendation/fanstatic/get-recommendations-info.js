var Module = function() {
    var self = {
        urlCheckUser: '',
        urlRecommendationCount: '',
        packageId: '',
        userLoggedIn: null,
        recommendationCount: null,
        recommendationCountSpan: null,
        submitBtn: null,
    }

    function init() {
        self.urlCheckUser = $('#package-data').data().urlCheckUser;
        self.urlRecommendationCount = $('#package-data').data().urlRecommendationCount;
        self.packageId = $('#package-data').data().packageId;
        self.recommendationCount = $('#count');
        self.recommendationCountSpan = $('.recommendation-count');
        self.userLoggedIn = $('#package-data').data().currentUser;
        self.submitBtn = $('#submit-btn');
    }

    function _setRecommendationCount() {
        $.ajax({
            url: self.urlRecommendationCount,
            cache: false,
            type: 'GET',
            error: function(error) {
                alert('Error fetching count.');
            },
            success: function(response) {
                const data = JSON.parse(response);
                self.recommendationCount.html(data.recommendation_count);
            }
        });
    }

    function _disableSubmitBtn() {
        $.ajax({
            url: self.urlCheckUser,
            cache: false,
            type: 'GET',
            error: function(error) {
                alert('Error checking user.');
            },
            success: function(response) {
                const data = JSON.parse(response);
                if (data.can_recommend === false) {
                    self.submitBtn.attr('disabled', 'true');
                } else {
                    self.submitBtn.removeAttr('disabled');
                }
            },
        });
    }

    function updateRecommendationInfo() {
        _disableSubmitBtn();
        _setRecommendationCount();
    }

    function run() {
        init();
        updateRecommendationInfo();
        self.recommendationCountSpan.removeClass('hidden');
    }

    return {run: run}
}()

var onSubmit = function(token) {
    $('#recommendation-form')[0].submit();
};

var onloadCallback = function() {
    const siteKey = $('#package-data').data().sitekey;
    grecaptcha.render('submit-btn', {
        'sitekey' : siteKey,
        'callback' : onSubmit
    });
    $('#submit-btn').attr('disabled', 'true');
};

window.addEventListener('load', (e) => {
    Module.run();
});
