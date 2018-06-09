/*<*******************

Copyright 2018 Juniper Networks, Inc. All rights reserved.
Licensed under the Juniper Networks Script Software License (the "License").
You may not use this script file except in compliance with the License, which is located at
http://www.juniper.net/support/legal/scriptlicense/
Unless required by applicable law or otherwise agreed to in writing by the parties, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

*******************>*/
(function ($) {
    "use strict";
    $.getJSON("/ListCAKCKN", function(data){
        for (var i = 0, len = data.length; i < len; i++) {
            console.log(data[i]);
    	    $(".table").append('<div class="row"> <div class="cell" data-title="Device A hostname">'+ data[i]['leaf_hostname']+'</div> <div class="cell" data-title="Device A interface">'+ data[i]['leaf_port'] + '</div> <div class="cell" data-title="Device B hostname">'+ data[i]['spine_hostname'] + '</div> <div class="cell" data-title="Device B interface">' + data[i]['spine_port'] + '</div><div class="cell" data-title="CKN">'+ data[i]['CKN'] + '</div><div class="cell" data-title="CAK">'+data[i].CAK+'</div></div>');
        }
    });
    

})(jQuery);
