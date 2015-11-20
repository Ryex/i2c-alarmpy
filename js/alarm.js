(function($){
    $.fn.moveTo = function(selector){
        return this.each(function(){
            var cl = $(this).clone();
            $(cl).appendTo(selector);
            $(this).remove();
        });
    };
})(jQuery);


function move_options(select) {
    var target = $(this).data('target');
    var bin = $(this).data('bin');
    var show = $("option:selected", this).data('show');
    $(target).children().moveTo(bin);
    $(show).moveTo(target);
}
