from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings
import json
import yt_dlp
import os
import requests
import time
import logging
from googletrans import Translator
import mimetypes

from .models import BlogPost

# Configure logging
logging.basicConfig(level=logging.DEBUG)

translator = Translator()

def main(request):
    return render(request, 'main.html')

@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data.get('link')  # Use get() to avoid KeyError
            if not yt_link:
                return JsonResponse({'error': 'Invalid data sent: link missing'}, status=400)
            
            title = yt_title(yt_link)
            if not title:
                return JsonResponse({'error': 'Failed to get YouTube video title'}, status=500)
            
            transcription = get_transcription(yt_link)
            if not transcription:
                return JsonResponse({'error': 'Failed to get transcript'}, status=500)

            # Translate to Urdu
            translated_content_urdu = translator.translate(transcription, src='en', dest='ur').text

            blog_content = generate_blog_from_transcription(transcription)
            if not blog_content:
                return JsonResponse({'error': 'Failed to generate blog article'}, status=500)

            new_blog_article = BlogPost.objects.create(
                user=request.user,
                youtube_title=title,
                youtube_link=yt_link,
                generated_content=blog_content,
            )
            new_blog_article.save()

            return JsonResponse({'content': blog_content, 'translated_content_urdu': translated_content_urdu})
        
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Invalid JSON data sent'}, status=400)
        
        except Exception as e:
            logging.error(f"Error generating blog: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
    
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def yt_title(link):
    try:
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            return info_dict.get('title', None)
    except Exception as e:
        logging.error(f"Error getting YouTube title: {e}")
        return None

@csrf_exempt
def download(request):
    try:
        link = request.GET.get('link')
        quality = request.GET.get('quality')
        
        if not link or not quality:
            return JsonResponse({'error': 'Missing link or quality parameter'}, status=400)
        
        audio_formats = {
            'audio': 'bestaudio/best',
        }
        video_formats = {
            'video_1080p': 'bestvideo[height<=1080]+bestaudio/best',
            'video_720p': 'bestvideo[height<=720]+bestaudio/best',
            'video_480p': 'bestvideo[height<=480]+bestaudio/best',
        }
        
        ydl_opts = {
            'format': audio_formats.get(quality) if quality in audio_formats else video_formats.get(quality),
            'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(id)s.%(ext)s'),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            download_file = ydl.prepare_filename(info_dict)
        
        mime_type, _ = mimetypes.guess_type(download_file)
        response = StreamingHttpResponse(open(download_file, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename={os.path.basename(download_file)}'
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def download_audio(link):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            audio_file = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        return audio_file
    
    except Exception as e:
        logging.error(f"Error downloading audio: {e}")
        return None

def get_transcription(link):
    try:
        audio_file = download_audio(link)
        if not audio_file:
            return None
        
        api_key = os.getenv('ASSEMBLYAI_API_KEY')
        if not api_key:
            logging.error("Please provide an API key via the ASSEMBLYAI_API_KEY environment variable or the global settings.")
            return None

        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        
        upload_url = "https://api.assemblyai.com/v2/upload"
        transcribe_url = "https://api.assemblyai.com/v2/transcript"
        
        with open(audio_file, 'rb') as f:
            upload_response = requests.post(upload_url, headers=headers, files={'file': f})
        
        if upload_response.status_code != 200:
            logging.error(f"Error uploading file: {upload_response.json()}")
            return None
        
        transcript_request = {
            "audio_url": upload_response.json().get('upload_url')
        }
        
        transcribe_response = requests.post(transcribe_url, headers=headers, json=transcript_request)
        if transcribe_response.status_code != 200:
            logging.error(f"Error requesting transcription: {transcribe_response.json()}")
            return None
        
        transcript_id = transcribe_response.json().get('id')
        
        while True:
            status_response = requests.get(f"{transcribe_url}/{transcript_id}", headers=headers)
            status_json = status_response.json()
            if status_json['status'] == 'completed':
                return status_json['text']
            elif status_json['status'] == 'failed':
                logging.error(f"Transcription failed: {status_json}")
                return None
            time.sleep(5)
    
    except Exception as e:
        logging.error(f"Error processing transcription: {e}")
        return None

def generate_blog_from_transcription(transcription):
    # This function can be expanded to generate more complex blog content
    return transcription

def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

def blog_details(request, pk):
    try:
        blog_article_detail = BlogPost.objects.get(id=pk)
        if request.user == blog_article_detail.user:
            return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
        else:
            return redirect('/')
    except BlogPost.DoesNotExist:
        return JsonResponse({'error': 'Blog article does not exist'}, status=404)

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
        
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        repeatPassword = request.POST.get('repeatPassword')

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except Exception as e:
                logging.error(f"Error creating account: {e}")
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match'
            return render(request, 'signup.html', {'error_message': error_message})
        
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('main')

@csrf_exempt
def translate_content(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        content = data.get('content')
        language = data.get('language')

        if content and language:
            translator = Translator()
            translation = translator.translate(content, dest=language)
            return JsonResponse({'translated_content': translation.text})
        else:
            return JsonResponse({'error': 'Invalid data'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
