pathname = window.location.pathname
function deletePost(id){
$.ajax({
    url: '/admin/posts/' + id,
    method: 'DELETE',
    success: function(result) {
        location.reload(true)
    },
    error: function(request,msg,error) {
        alert(error)
    }
});
}

function vote(input){
id = input.split('_')[1];
method = input.split('_')[0];
data = {"md5":id,"vote":method};
$.ajax({
    url: '/vote',
    method: 'POST',
    data: data,
    success: function(result) {
        old = Number(document.getElementById('vote_count_'+id).textContent);
        if (method == 'up'){
                document.getElementById('vote_count_'+id).textContent = old + 1;
        } else {
                document.getElementById('vote_count_'+id).textContent = old - 1;
        }

        console.log(true)
    },
    error: function(request,msg,error) {
        console.log(error)    }
});
}


$(".delete").click(function(){
        deletePost($(this).attr("id"));
    });



$( ".leftside" ).on( "click",".upvote", function() {
  vote( $( this ).attr("id") );
});
$( ".leftside" ).on( "click",".downvote", function() {
  vote( $( this ).attr("id") );
});


$('.leftside').infiniteScroll({
  // options
  path: '.page-next',
  append: '.leftside',
  history: 'replace',
  //hideNav: '.pagination',
})

$(document).ready(function(){

	var back_to_top_button = ['<a href="#top" class="backToTop">Back to top</a>'].join("");
	$("body").append(back_to_top_button)

	$(".backToTop").hide();

	$("#reportForm").submit(function(event){
                submitForm();
                return false;
        });

     	$("#doxForm").submit(function(event){
                submitDoxForm();
                return false;
        });

	$(function () {
		$(window).scroll(function () {
			if ($(this).scrollTop() > 100) {
				$('.backToTop').fadeIn();
			} else {
				$('.backToTop').fadeOut();
			}
		});

		$('.backToTop').click(function () {
			$('body,html').animate({
				scrollTop: 0
			}, 800);
			return false;
		});
	});

});


$("#modalContactForm").on('show.bs.modal', function(){

    document.getElementById('form34').value=pathname.split('/')[2];
 ;
 });

 $("#doxForm").on('show.bs.modal', function(){

    document.getElementById('dox1').value=pathname.split('/')[2];
 ;
 });


function submitForm(){
    $.ajax({
        type: "POST",
        url: '/report',
        cache:false,
        data: $('form#reportForm').serializeJSON(),
        contentType: "application/json",
        success: function(response){
            $("#modalContactForm").modal('hide')
            window.location.reload(true)
        },
        error: function(response){
            window.location.reload(true);
        }
    });}

function submitDoxForm(){
    $.ajax({
        type: "POST",
        url: '/girl/dox',
        cache:false,
        data: $('form#doxForm').serializeJSON(),
        contentType: "application/json",
        success: function(response){
            $("#doxFormModal").modal('hide')
            window.location.reload(true)
        },
        error: function(response){
            window.location.reload(true);
        }
    });}
