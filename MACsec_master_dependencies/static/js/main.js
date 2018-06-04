(function ($) {
    "use strict";
    $.getJSON("http://172.27.169.123:8080/ListCAKCKN", function(data){
        for (var i = 0, len = data.length; i < len; i++) {
            console.log(data[i]);
    	    $(".table").append('<div class="row"> <div class="cell" data-title="Device A hostname">'+ data[i]['leaf_hostname']+'</div> <div class="cell" data-title="Device A interface">'+ data[i]['leaf_port'] + '</div> <div class="cell" data-title="Device B hostname">'+ data[i]['spine_hostname'] + '</div> <div class="cell" data-title="Device B interface">' + data[i]['spine_port'] + '</div><div class="cell" data-title="CKN">'+ data[i]['CKN'] + '</div><div class="cell" data-title="CAK">'+data[i].CAK+'</div></div>');
        }
    });
    

})(jQuery);
