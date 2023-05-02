$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

function AjaxResult(data){
	return $($.parseHTML(data.html)).filter('*').show();
	}

function ReplaceBlock(from, to, callback){
    from.slideUp('normal', function(){
        $(this).replaceWith(to.hide());
        to.slideDown('fast');
    if (callback && typeof(callback) === "function") {
                    callback();
                }
    });
}

function FavoriteSet(path, id){
    data = {'pk': id}
    $.post(path, data, function (data) {
        if (data.success) {
            if (data.is_favorite) {
                $('#favorite-'+id).text('favorite');
            }
            else {
                $('#favorite-'+id).text('favorite_border');
            }
        }
    });
}
function Like(id, mode, url){
    var karma = $("#"+'karma-'+id);
    var liked = $("#"+'liked-'+id);
    var disliked = $("#"+'disliked-'+id);
    $.ajax({type: 'POST', url: url, data: {mode: mode },
        success: function(data) {
            if (data.success) {
                karma.text(data.karma)
                if (data.liked) {
                    liked.addClass('active-like');
                    liked.css('color', '#90c990')
                }
                else {
                    liked.removeClass('active-like');
                    liked.css('color', '#c9c9c9')
                }
                if (data.disliked) {
                    disliked.addClass('active-dislike');
                    disliked.css('color', '#c99090')
                }
                else {
                    disliked.removeClass('active-dislike');
                    disliked.css('color', '#c9c9c9')
                }
            }
        }
    });
}
function DeleteMessage(id, url){
    $.post( url, {} , function(data) {
	    if (data.success) {
            if($('#message-subject-'+id).hasClass('font-weight-bold')) {
                var unread = Number($('#unread-message').text()) - 1;
                $('#unread-message').text(unread);
                if (unread == 0) {
                    $('#unread-msg').css("display", "none");
                }
            }
            var total = Number($('#total-message').text()) - 1;
            $('#total-message').text(total);
	        $("#message-"+id).slideUp('slow' ,function() {
        	$("#message-"+id).remove();
        });
        }
	});
}