
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
from pytube import YouTube
import os
import assemblyai as aai
from .models import BlogPost

# View for rendering the index page, accessible only to logged-in users
def main(request):
    return render(request, 'main.html')
@login_required
def index(request):
    """
    Renders the index page.
    
    Returns:
        Rendered index page.
    """
    return render(request, 'index.html')

# View for generating blog content from a YouTube video link
@csrf_exempt
def generate_blog(request):
    """
    Generates blog content from a YouTube video link.
    
    If the request method is POST, it extracts the YouTube link from the request data,
    retrieves the video title and transcript, generates blog content from the transcript,
    saves the blog article to the database, and returns the generated content as a response.
    If the request method is not POST, it returns an error response.
    
    Returns:
        JSON response containing the generated blog content or an error message.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)

        # get YouTube video title
        title = yt_title(yt_link)

        # get transcript from the YouTube video
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "Failed to get transcript"}, status=500)

        # generate blog content from the transcript
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': "Failed to generate blog article"}, status=500)

        # save blog article to database
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            generated_content=blog_content,
        )
        new_blog_article.save()

        # return blog article as a response
        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

# Helper function to get the YouTube video title
def yt_title(link):
    """
    Retrieves the title of a YouTube video.
    
    Args:
        link (str): The YouTube video link.
    
    Returns:
        str: The title of the YouTube video.
    """
    yt = YouTube(link)
    title = yt.title
    return title

# Helper function to download audio from a YouTube video
def download_audio(link):
    """
    Downloads audio from a YouTube video.
    
    Args:
        link (str): The YouTube video link.
    
    Returns:
        str: The path to the downloaded audio file.
    """
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

# Helper function to get transcription from the audio file using AssemblyAI
def get_transcription(link):
    """
    Retrieves transcription from an audio file using AssemblyAI.
    
    Args:
        link (str): The YouTube video link.
    
    Returns:
        str: The transcription text.
    """
    audio_file = download_audio(link)
    aai.settings.api_key = "84d29c9d45e04dc2870c581dfd197bff"  # Your AssemblyAI API key

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text

# Helper function to generate blog content from the transcription
def generate_blog_from_transcription(transcription):
    """
    Generates blog content from a transcription.
    
    Args:
        transcription (str): The transcription text.
    
    Returns:
        str: The generated blog content.
    """
    # For now, simply return the transcription itself as the blog content
    return transcription

# View for rendering the list of blog articles
def blog_list(request):
    """
    Renders the list of blog articles.
    
    Args:
        request: The HTTP request.
    
    Returns:
        Rendered page displaying the list of blog articles.
    """
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

# View for rendering details of a specific blog article
def blog_details(request, pk):
    """
    Renders details of a specific blog article.
    
    Args:
        request: The HTTP request.
        pk (int): The primary key of the blog article.
    
    Returns:
        Rendered page displaying details of the specified blog article.
    """
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')

# View for user login
def user_login(request):
    """
    Handles user login.
    
    Args:
        request: The HTTP request.
    
    Returns:
        Rendered login page with error message if login fails.
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
        
    return render(request, 'login.html')

# View for user signup
def user_signup(request):
    """
    Handles user signup.
    
    Args:
        request: The HTTP request.
    
    Returns:
        Rendered signup page with error message if signup fails.
    """
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message':error_message})
        
    return render(request, 'signup.html')

# View for user logout
def user_logout(request):
    """
    Handles user logout.
    
    Args:
        request: The HTTP request.
    
    Returns:
        Redirects to the homepage after logout.
    """
    logout(request)
    return redirect('main')
