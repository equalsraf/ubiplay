$(document).ready(function() {

		function onError(resp, http_status, error) {
			try {
				var json = $.parseJSON(resp.responseText);
				if ('error' in json) {
					$('#error .msg').text(json.error);
				} else {
					$('#error .msg').text('Error calling remote server');
				}
			} catch (e) {
				$('#error .msg').text('Error calling remote server');
			}
			$('#error').show();
			$('#span_addsource').removeClass("glyphicon-refresh glyphicon-refresh-animate").addClass("glyphicon-plus");
			$('.btn-success').removeClass("btn-success").addClass("btn-primary");

		}

		function onSuccess(json, http_status, error) {
			// Clean up after a successful request
			$('#addsource_url').val('');
			$('#error').hide();
			$('#span_addsource').removeClass("glyphicon-refresh glyphicon-refresh-animate").addClass("glyphicon-plus");
			$('.btn-success').removeClass("btn-success").addClass("btn-primary");
			retrivePlaylist();
		}

		function retrivePlaylist(){
				$.ajax({
						url: "/playlistinfo",
						contentType: 'application/json',
						dataType: 'json',
						error: onError,
						success: populatePlaylist,
				});
				clearTimeout(next_event);
				next_event = setTimeout(retrivePlaylist,30000);
		}

		$('.close').on('click',function(){
		  $(this).parent().hide();
		});

		function retriveCurrent(){
				$.ajax({
						url: "/status",
						contentType: 'application/json',
						dataType: 'json',
						error: onError,
						success: setCurrent,
				});
		}

		function populatePlaylist(json, http_status, error){
			var items = [];
		    $.each(json, function (id, data) {
		        items.push('<li class="list-group-item" id="' + data.id + '">' 
		        	+ (data.title||"No title") 
		        	+ '<span class="remove-song glyphicon glyphicon-remove pull-right" style="display:none;" aria-hidden="true"></span>'
		        	+ '</li>');
		    });  
		    $('#playlist_list').html(items.join(''));
		    retriveCurrent();
		    $('.list-group-item').on("dblclick",function(ev) {
				$.ajax({
						url: "/playid",
						contentType: 'application/json',
						data: JSON.stringify({songid: this.id}),
						dataType: 'json',
						type: 'POST',
						error: onError,
						success: onSuccess,
				});
				$(this).css('background-color', '#99FFCC');
			});
			$('.list-group-item').on("mouseover",function(ev) {
				$(this).children('.remove-song').show();
			});
			$('.list-group-item').on("mouseout",function(ev) {
				$(this).children('.remove-song').hide();
			});
			$('.remove-song').on("click",function(ev) {
				$.ajax({
						url: "/deleteid",
						contentType: 'application/json',
						data: JSON.stringify({songid: $(this).parent().attr('id')}),
						dataType: 'json',
						type: 'POST',
						error: onError,
						success: onSuccess,
				});
			});
		}

		function setCurrent(json, http_status, error){		    
		    $('#'+json.songid).css('background-color', '#99CCFF');
		    $('#volume').attr("aria-valuenow",json.volume);
		    $('#volume').attr("style","width: " + json.volume + "%;");
		    $('#volume').text(json.volume + "%");
		}

		$('#button_previous').on("click", function(ev) {
				$.ajax({
						url: "/previous",
						error: onError,
						success: onSuccess,
				});
				$(this).removeClass("btn-primary").addClass("btn-success");
		});

		$('#button_play').on("click", function(ev) {
				$.ajax({
						url: "/play",
						error: onError,
						success: onSuccess,
				});
				$(this).removeClass("btn-primary").addClass("btn-success");
		});

		$('#button_pause').on("click", function(ev) {
				$.ajax({
						url: "/pause",
						error: onError,
						success: onSuccess,
				});
				$(this).removeClass("btn-primary").addClass("btn-success");
		});

		$('#button_stop').on("click", function(ev) {
				$.ajax({
						url: "/stop",
						error: onError,
						success: onSuccess,
				});
				$(this).removeClass("btn-primary").addClass("btn-success");
		});

		$('#button_next').on("click", function(ev) {
				$.ajax({
						url: "/next",
						error: onError,
						success: onSuccess,
				});
				$(this).removeClass("btn-primary").addClass("btn-success");
		});

		$('#button_clear_playlist').on("click", function(ev) {
				$.ajax({
						url: "/clear",
						error: onError,
						success: onSuccess,
				});
				$(this).removeClass("btn-primary").addClass("btn-success");
		});

		$('#volume').parent().on("click", function(ev){
			var x;
			if(ev.offsetX==undefined) // this works for Firefox
			{
				x = ev.pageX-$('#volume').offset().left;
			}
			else	// works in Google Chrome
			{
				x = ev.offsetX;
			}
			var volume = Math.round(100*x/$(this).width());
			$.ajax({
						url: "/setvol",
						contentType: 'application/json',
						data: JSON.stringify({volume: volume}),
						dataType: 'json',
						type: 'POST',
						error: onError,
						success: onSuccess,
				});
		});

		$('#addsource_url').keypress(function (ev) {
			 var key = ev.which;
			 if(key == 13)  // the enter key code
			  {
			    $('#button_addsource').click();
			    return false;  
			  }
			});

		$('#button_addsource').on("click", function(ev) {
				var url = $('#addsource_url').val();
				if (!url) {
						return;
				}

				$.ajax({
						url: "/ydl_addurl",
						contentType: 'application/json',
						data: JSON.stringify({url: url}),
						dataType: 'json',
						type: 'POST',
						error: onError,
						success: onSuccess,
				});
				$('#span_addsource').removeClass("glyphicon-plus").addClass("glyphicon-refresh glyphicon-refresh-animate");
		});

		$('#playlist_list').sortable({ 
    		stop: function(event, ui) {
        		var pos = ui.item.index();
        		var id = ui.item.attr("id");
				$.ajax({
						url: "/moveid",
						contentType: 'application/json',
						data: JSON.stringify({id: id, pos: pos}),
						dataType: 'json',
						type: 'POST',
						error: onError,
						success: onSuccess,
				});
    		}
		}).disableSelection();

		var next_event = setTimeout(retrivePlaylist,0);
});
