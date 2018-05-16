(function ($) {
    "use strict";
    $.getJSON("http://172.27.169.123:8080/ListCAKCKN", function(data){
        for (var i = 0, len = data.length; i < len; i++) {
            console.log(data[i]);
    	    $(".table").append('<div class="row"> <div class="cell" data-title="Left chassis ID">'+ data[i]['leaf_ID']+'</div> <div class="cell" data-title="Left interface">'+ data[i]['leaf_port'] + '</div> <div class="cell" data-title="Right chassis ID">'+ data[i]['spine_ID'] + '</div> <div class="cell" data-title="Right interface">' + data[i]['spine_port'] + '</div><div class="cell" data-title="CKN">'+ data[i]['CKN'] + '</div><div class="cell" data-title="CAK">'+data[i].CAK+'</div></div>');
        }
    });
    

})(jQuery);
