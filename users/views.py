from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from users.forms import UserRegistrationForm
from .models import UserRegistrationModel
import os, re, mimetypes
import google.generativeai as genai

# ---------------- Gemini Config ----------------
GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", None) or \
                 os.getenv("GEMINI_API_KEY") or \
                 ""
genai.configure(api_key=GEMINI_API_KEY)


# ---------------- Base ----------------
def base(request):
    return render(request, 'base.html')


# ---------------- Register ----------------
def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Registered successfully')
            return render(request, 'UserRegistration.html')
        else:
            messages.error(request, '❌ Email/Mobile already exists')
    else:
        form = UserRegistrationForm()
    return render(request, 'UserRegistration.html', {'form': form})


# ---------------- Login ----------------
def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('password')
        try:
            user = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            if user.status == "activated":
                request.session['id'] = user.id
                request.session['loggeduser'] = user.name
                return redirect('UserHome')
            else:
                messages.error(request, '⚠️ Account not activated')
        except UserRegistrationModel.DoesNotExist:
            messages.error(request, '❌ Invalid Login/Password')
    return render(request, 'UserLogin.html')


# ---------------- User Home ----------------
def UserHome(request):
    return render(request, 'users/UserHome.html')


# ---------------- WanderGenie Tourism Guide ----------------
def wander_genie(request):
    """
    AI-powered tourist guide using Gemini
    """
    user_query = None
    response_text = None

    if request.method == "POST":
        user_query = request.POST.get("tour_query", "").strip()
        if not user_query:
            messages.error(request, "Please enter a tourist query (e.g., 'Tell me about Taj Mahal').")
        else:
            try:
                prompt = f"""
You are **WanderGenie**, a smart tourism assistant.
Provide immersive travel guidance based on the user query.

Query: {user_query}

Respond in this format:
✨ Description: <short engaging intro about the place>
📜 Significance: <historical/cultural/unique facts>
💡 Travel Tips: <best time to visit, things to do, food suggestions>
                """
                model = genai.GenerativeModel("models/gemini-2.5-flash")
                response = model.generate_content(prompt)
                response_text = response.text.strip()

            except Exception as e:
                response_text = f"⚠️ Error: {str(e)}"

    return render(request, "users/wander_genie.html", {
        "user_query": user_query,
        "response_text": response_text
    })


# ---------------- Landmark Image Analyzer ----------------
def landmark_analyzer(request):
    """
    Upload a landmark image -> AI describes and gives tourist info
    """
    analysis_result = None
    if request.method == "POST" and request.FILES.get("landmark_image"):
        image_file = request.FILES["landmark_image"]

        try:
            prompt = """
You are WanderGenie, an AI tourism guide.
Analyze the uploaded landmark image and provide:

✨ Landmark Name & Description
📜 Historical / Cultural Significance
💡 Visitor Tips
"""

            mime_type, _ = mimetypes.guess_type(image_file.name)
            image_data = {
                "mime_type": mime_type or "image/jpeg",
                "data": image_file.read()
            }

            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content([prompt, image_data])
            analysis_result = response.text.strip()

        except Exception as e:
            analysis_result = f"⚠️ Error: {str(e)}"

    return render(request, "users/landmark_analyzer.html", {
        "analysis_result": analysis_result
    })
