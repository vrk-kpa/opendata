/*
 * (C) Copyright 2015 CoNWeT Lab., Universidad Politécnica de Madrid
 *
 * This file is part of CKAN Data Requests Extension.
 *
 * CKAN Data Requests Extension is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * CKAN Data Requests Extension is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
 * License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with CKAN Data Requests Extension. If not, see
 * <http://www.gnu.org/licenses/>.
 *
 */

(function() {
    
    var UPDATE_COMMENT_BASIC_ID = 'update-comment-';

    // Capture all the update buttons
    $("[id^=" + UPDATE_COMMENT_BASIC_ID + "]").on('click', function(e) {
        comment_id = $(this).attr('id').replace(UPDATE_COMMENT_BASIC_ID, '');
        
        // Set comment in the textarea and the ID in the hidden input
        $('#comment-id').val(comment_id);
        $('#field-comment').val($('#comment-' + comment_id).text().trim());

        // Hide and show buttons
        $('#datarequest-comment-update-discard').removeClass('hide');
        $('#datarequest-comment-update').removeClass('hide');
        $('#datarequest-comment-add').addClass('hide');
    });

    // Capute the discard button
    $('#datarequest-comment-update-discard').on('click', function(e) {
        // Remove the values
        $('#comment-id').val('');
        $('#field-comment').val('');

        // Hide and show buttons
        $('#datarequest-comment-update-discard').addClass('hide');
        $('#datarequest-comment-update').addClass('hide');
        $('#datarequest-comment-add').removeClass('hide');

        // Prevent default
        e.preventDefault();
    })
})();