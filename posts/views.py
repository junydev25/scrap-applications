from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from posts.forms import CommentForm, PostForm
from posts.models import Post, Comment, PostImage, HashTag


# Create your views here.
def feeds(request):
    if not request.user.is_authenticated:
        return redirect("users:login")

    posts = Post.objects.all()
    comment_form = CommentForm()
    context = {"posts": posts,
               "comment_form": comment_form,}
    return render(request, "posts/feeds.html", context)


@require_POST
def comment_add(request):
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.save()

        url_next = request.GET.get("next") or reverse("posts:feeds") + f"#post-{comment.post.id}"
        return HttpResponseRedirect(url_next)

@require_POST
def comment_delete(request, comment_id):
    comment = Comment.objects.get(id=comment_id)
    if comment.user == request.user:
        comment.delete()
        url = reverse("posts:feeds") + f"#post-{comment.post.id}"
        return HttpResponseRedirect(url)
    else:
        return HttpResponseForbidden("이 댓글을 삭제할 권한이 없습니다.")

def post_add(request):
    form = PostForm()
    if request.method == "POST":
        form = PostForm(data=request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

            for image_file in request.FILES.getlist("image"):
                PostImage.objects.create(
                    post=post,
                    photo=image_file,
                )

            tag_string = request.POST.get("tags")
            if tag_string:
                tag_names = [tag_name.strip() for tag_name in tag_string.split(",")]
                for tag_name in tag_names:
                    tag, _ = HashTag.objects.get_or_create(name=tag_name)
                    post.tags.add(tag)

            url = reverse("posts:feeds") + f"#post-{post.id}"
            return HttpResponseRedirect(url)
    context = {"form": form}

    return render(request, "posts/post_add.html", context)

def tags(request, tag_name):
    try:
        tag = HashTag.objects.get(name=tag_name)
    except HashTag.DoesNotExist:
        posts = Post.objects.none()
    else:
        posts = Post.objects.filter(tags=tag)

    context = {
        "tag_name": tag_name,
        "posts": posts,
    }

    return render(request, 'posts/tags.html', context)

def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    comment_form = CommentForm()
    context = {
        "post": post,
        "comment_form": comment_form,
    }
    return render(request, "posts/post_detail.html", context)

def post_like(request, post_id):
    post = Post.objects.get(id=post_id)
    user = request.user

    if user.like_posts.filter(id=post.id).exists():
        user.like_posts.remove(post)
    else:
        user.like_posts.add(post)

    url_next = request.GET.get("next") or reverse("posts:feeds") + f"#post-{post.id}"
    return HttpResponseRedirect(url_next)