I used assembly ai api for transciprting youtube video speech into text and use python library as well for first download audio of this video file
-------------------------------------------------------
aiohttp==3.8.4
aiosignal==1.3.1
anyio==3.6.2
arabic-reshaper==3.0.0
asgiref==3.6.0
asn1crypto==1.5.1
assemblyai==0.17.0
async-timeout==4.0.2
attrs==22.2.0
cachetools==4.2.4
certifi==2022.12.7
cffi==1.15.1
charset-normalizer==3.0.1
click==8.1.3
cryptography==39.0.2
cssselect2==0.7.0
defusedxml==0.7.1
Django==4.1.7
django-allauth==0.54.0
django-extensions==3.2.1
django-googledrive-storage==1.6.0
django-storages==1.13.2
fastapi==0.94.1
frozenlist==1.3.3
google-api-core==2.10.2
google-api-python-client==2.97.0
google-auth==1.35.0
google-auth-httplib2==0.1.0
googleapis-common-protos==1.60.0
h11==0.14.0
html5lib==1.1
httpcore==0.17.3
httplib2==0.22.0
httpx==0.24.1
idna==3.4
iniconfig==2.0.0
lxml==4.9.2
multidict==6.0.4
openai==0.27.5
psycopg2==2.9.6
psycopg2-binary==2.9.6
pytube==15.0.0
requests==2.28.2
sqlparse==0.4.3
webencodings==0.5.1
websockets==11.0.3
-----------------------------------------------------------------------------------------------
python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

deactivate

source venv/bin/activate  # Use `venv\Scripts\activate` on Windows
pip install --upgrade httpcore

pip install httpcore==0.13.6

pip install --upgrade googletrans


pip install googletrans==4.0.0-rc1

pip install -r requirements.txt

python manage.py runserver
--------------------------------------------------------------------------------------------
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

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)

        # get yt title
        title = yt_title(yt_link)

        # get transcript
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "Failed to get transcript"}, status=500)

        # Generate blog content from the transcript
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': "Failed to generate blog article"}, status=500)

        # Save blog article to database
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            generated_content=blog_content,
        )
        new_blog_article.save()

        # Return blog article as a response
        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    # Your AssemblyAI API key
    aai.settings.api_key = "84d29c9d45e04dc2870c581dfd197bff"

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text

def generate_blog_from_transcription(transcription):
    # No OpenAI code here, only AssemblyAI
    # Process the transcription here as needed for generating the blog content
    return "Mp3 file has been downloaded"

def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
        
    return render(request, 'login.html')

def user_signup(request):
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

def user_logout(request):
    logout(request)
    return redirect('/')

------------------------------------------------------------------------------------------------------


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
            return redirect('/')
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
    return redirect('/')
