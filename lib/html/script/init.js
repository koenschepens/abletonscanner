$(document).ready(function() {
    $("#topnav ul li").each(function(){
        $li = $(this);
        var href = $li.find('a').attr("href");
        var current_path = document.location.pathname.replace(/%20/g, " ");

        if(current_path.split(".")[0].indexOf(href.split(".")[0]) >= 0
            ||
            current_path == href) {
            $li.addClass("active");
        }
        else
        {
            $li.removeClass("active");
        }
    });

    $(".toggler").each(function(){
        $(this).html("<span class='pl'>[+]</span> " + $(this).html());
    });

    $(".toggler").on("click", function(e)
    {
        $header = $(this);
        $target = $("#" + $(this).data().target);
        $target.toggle(300, function(){
            if($target.css("display") == "block")
            {
                $header.find(".pl").replaceWith("<span class='pl'>[-]</span>");
            }
            else
            {
                $header.find(".pl").replaceWith("<span class='pl'>[+]</span>");
            }
        });

    });
});